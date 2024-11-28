var database = {
	// 远程服务器列表
	cloudDatabaseList: [],
	// 远程服务器表格实例
	dbCloudServerTable: null,
	// 初始化
	init: function () {
		this.event();
		var type = this.getType();
		$('.database-pos .tabs-item[data-type="' + type + '"]').trigger('click');
	},
	// 事件
	event: function () {
		var that = this;
		// 切换分类
		$('.database-pos .tabs-item').click(function () {
			var index = $(this).index();
			var type = $(this).data('type');
			bt.set_cookie('db_page_model', type);
			$(this).addClass('active').siblings().removeClass('active');
			$('.db_table_view .tab-con .tab-con-block').eq(index).removeClass('hide').siblings().addClass('hide');
			// 获取远程数据库
			that.getCloudDatabase(function () {
				that.getDatabaseList();
			});
		});

		// 安装数据库插件
		$('.prompt_description').on('click', '.btn-install-mysql', function () {
			var db_type = that.getType();
			if (db_type == 'pgsql') {
				// 判断是否安装插件
				bt.soft.get_soft_find('pgsql_manager', function (rdata) {
					for (var i = 0; i < rdata.versions.length; i++) {
						// 判断是否安装版本
						if (rdata.versions[i].setup == true) {  
							bt.soft.set_lib_config('pgsql_manager', 'PostgreSQL管理器')
							break;
						}else{
							bt.soft.install('pgsql_manager')
							break;
						}
					}
				});
			} else {
				bt.soft.install(db_type);
			}
		});

		// 添加远程数据库
		$('.prompt_description').on('click', '.btn-add-cloud-server', function () {
			that.render_db_cloud_server_view();
		});

		redis.event();
	},
	// 获取当前分类
	getType: function () {
		return bt.get_cookie('db_page_model') || 'mysql';
	},
	// 通过分类获取当前数据库
	getDatabaseList: function (config) {
		var type = this.getType();
		switch (type) {
			case 'mysql':
				mysql.getDatabaseList(config);
				break;
			case 'sqlserver':
				sqlserver.getDatabaseList(config);
				break;
			case 'mongodb':
				bt_tools.send({
					url: 'database/' + type + '/get_root_pwd'
				}, function (_status) {
					mongodb.mongoDBAccessStatus = _status.authorization == 'enabled' ? true : false;
					mongodb.getDatabaseList(config);
				});
				break;
			case 'redis':
				redis.getDatabaseList(config);
				break;
			case 'pgsql':
				pgsql.getDatabaseList(config);
				break;
		}
	},
	// 获取远程数据库
	getCloudDatabase: function (callback) {
		var that = this;
		var type = this.getType();
		var params = {
			url: 'database?action=GetCloudServer',
			data: { type: type },
		};
		if (type != 'mysql') {
			params.url = 'database/' + type + '/GetCloudServer';
			params.data = { data: JSON.stringify({ type: type }) };
		}
		bt_tools.send(
			params,
			function (cloudData) {
				that.cloudDatabaseList = cloudData;
				// 是否安装本地或远程服务器
				if (cloudData.length <= 0) {
					var tips = lan.database.cloud_not_config1 + ', <a class="btlink btn-install-mysql">Click install</a> | <a class="btlink btn-add-cloud-server">' + lan.database.add_cloud_btn + '</a>';
					if (type == 'sqlserver') tips = lan.database.cloud_not_config2 + ', <a class="btlink btn-add-cloud-server">' + lan.database.add_cloud_btn + '</a>';
					$('.mask_layer').removeClass('hide');
					$('.prompt_description').html(tips);
				} else {
					$('.mask_layer').addClass('hide');
				}
				// 渲染远程数据库列表
				that.renderCloudServerSelect();
				// 渲染远程数据库表格
				that.renderCloudServerTable();
				callback && callback(cloudData);
			},
			lan.database.get_cloud_list_tips
		);
	},
	// 获取程服务器列表
	getCloudServerList: function (callback) {
		var list = this.cloudDatabaseList;
		var cloudList = [];
		$.each(list, function (index, item) {
			var ps = item.ps;
			var host = item.db_host;
			if (!ps || !host) return;
			var tips = ps != '' ? ps + ' (' + host + ')' : host;
			cloudList.push({ title: tips, value: item.id });
		});
		callback && callback(cloudList);
	},
	// 渲染远程数据库选择框
	renderCloudServerSelect: function () {
		var that = this;
		var type = this.getType();
		var idMap = {
			mysql: '#bt_database_table',
			sqlserver: '#bt_sqldatabase_table',
			mongodb: '#bt_mongodb_table',
			pgsql: '#bt_pgsql_table',
		}
		var id = idMap[type];
		if ($(id + ' .database_type_select_filter').length == 0) {
			$(id + ' .bt_search').before('<select class="bt-input-text mr5 database_type_select_filter" style="width: 120px" name="db_type_filter_' + type + '"></select>');
			$(id + ' .database_type_select_filter').change(function () {
				that.getDatabaseList({ isInit: true });
			});
		}
		var option = '<option value="all">' + lan.public.all + '</option>';
		$.each(this.cloudDatabaseList, function (index, item) {
			var tips = item.ps != '' ? item.ps : item.db_host;
			option += '<option value="' + item.id + '">' + tips + '</option>';
		});
		$(id + ' .database_type_select_filter').html(option);
	},
	// 打开远程服务器列表弹框
	open_cloud_server: function () {
		var that = this;
		var $layer = null;
		bt_tools.open({
			title: lan.database.cloud_server_list,
			area: '860px',
			btn: false,
			skin: 'databaseCloudServer',
			content: '<div id="db_cloud_server_table" class="pd20"></div>',
			success: function (layero) {
				$layer = layero;
				this.getServerTable();
				that.getCloudDatabase();
			},
			getServerTable: function () {
				var _that = this;
				that.dbCloudServerTable = bt_tools.table({
					el: '#db_cloud_server_table',
					data: [],
					default: lan.database.cloud_server_empty,
					height: 300,
					column: [
						{
							fid: 'db_host',
							title: lan.database.server_address,
							width: 100,
							template: function (item) {
								return '<span class="flex"><span class="text-overflow" title="' + item.db_host + '">' + item.db_host + '</span></span>';
							},
						},
						{
							fid: 'db_port',
							width: 80,
							title: lan.database.port,
						},
						{
							fid: 'db_type',
							width: 110,
							title: lan.database.type,
						},
						{
							fid: 'db_user',
							width: 90,
							title: lan.database.user,
						},
						{
							fid: 'db_password',
							width: 190,
							type: 'password',
							title: lan.database.add_pass,
							copy: true,
							eye_open: true,
						},
						{
							fid: 'ps',
							title: lan.database.add_ps,
							template: function (item) {
								var ps = item.ps;
								return '<span class="flex"><span class="text-overflow" title="' + ps + '">' + ps + '</span></span>';
							},
						},
						{
							type: 'group',
							width: 130,
							title: lan.database.operation,
							align: 'right',
							group: [
								{
									title: 'Get DB',
									event: function (row) {
										bt.database.sync_database(row.id, function (rdata) {
											if (rdata.status) {
												that.getDatabaseList();
											}
										});
									},
								},
								{
									title: lan.public.edit,
									event: function (row) {
										that.render_db_cloud_server_view(row, true);
									},
								},
								{
									title: lan.public.del,
									event: function (row) {
										that.del_db_cloud_server(row);
									},
								},
							],
						},
					],
					tootls: [
						{
							type: 'group',
							positon: ['left', 'top'],
							list: [
								{
									title: lan.public.add + ' ' + lan.database.cloud_server,
									active: true,
									event: function () {
										that.render_db_cloud_server_view();
									},
								},
							],
						},
					],
					success: function (config) {
						that.cloudDatabaseList = config.data;
						_that.setLayerCenter();
					},
				});
			},
			// 设置弹窗居中
			setLayerCenter: function () {
				if (!$layer) return;
				var height = $(window).height();
				var layerHeight = $layer.height();
				var top = (height - layerHeight) / 2;
				$layer.css('top', top);
			},
		});
	},
	// 渲染远程数据库表格
	renderCloudServerTable: function () {
		if (this.dbCloudServerTable) {
			var list = this.cloudDatabaseList;
			var data = [];
			for (var i = 0; i < list.length; i++) {
        var element = list[i];
        if(element.id == 0) continue
        data.push(element)
      }
			this.dbCloudServerTable.$reader_content(data);
		}
	},
	// 添加/编辑远程服务器视图
	render_db_cloud_server_view: function (config, is_edit) {
		var that = this;
		if (!config) {
			var type = this.getType();
			var dataMap = {
				mysql: { user: 'root', port: '3306' },
				sqlserver: { user: 'sa', port: '1433' },
				redis: { user: 'root', port: '6379' },
				mongodb: { user: 'root', port: '27017' },
				pgsql: { user: 'postgres', port: '5432' },
			}
			config = {
				db_host: '',
				db_port: dataMap[type].port,
				db_user: '',
				db_password: '',
				db_user: dataMap[type].user,
				ps: '',
			};
		}
		var title = is_edit ? lan.public.edit : lan.public.add;
		bt_tools.open({
			title: title + ' ' + lan.database.cloud_server,
			area: '460px',
			btn: [lan.public.save, lan.public.cancel],
			skin: 'addCloudServerProject',
			content: {
				class: 'pd20',
				form: [
					{
						label: lan.database.server_address,
						group: {
							type: 'text',
							name: 'db_host',
							width: '260px',
							value: config.db_host,
							placeholder: lan.database.input_server_address,
							event: function () {
								$('[name=db_host]').on('input', function () {
									$('[name=db_ps]').val($(this).val());
								});
							},
						},
					},
					{
						label: lan.database.port,
						group: {
							type: 'number',
							name: 'db_port',
							width: '260px',
							value: config.db_port,
							placeholder: lan.database.input_port,
						},
					},
					{
						label: lan.database.user,
						group: {
							type: 'text',
							name: 'db_user',
							width: '260px',
							value: config.db_user,
							placeholder: lan.database.input_username,
						},
					},
					{
						label: lan.database.add_pass,
						group: {
							type: 'text',
							name: 'db_password',
							width: '260px',
							value: config.db_password,
							placeholder: lan.database.input_password,
						},
					},
					{
						label: lan.database.add_ps,
						group: {
							type: 'text',
							name: 'db_ps',
							width: '260px',
							value: config.ps,
							placeholder: lan.database.server_note,
						},
					},
					{
						group: {
							type: 'help',
							style: { 'margin-top': '0' },
							list: [lan.database.remote_help_1, lan.database.remote_help_2, lan.database.remote_help_3, lan.database.remote_help_4],
						},
					},
				],
			},
			yes: function (form, indexs) {
				if (form.db_host == '') return layer.msg(lan.database.input_server_address, { icon: 2 });
				if (form.db_port == '') return layer.msg(lan.database.input_port, { icon: 2 });
				if (form.db_user == '') return layer.msg(lan.database.input_username, { icon: 2 });
				if (form.db_password == '') return layer.msg(lan.database.input_password, { icon: 2 });

				if (is_edit) form['id'] = config['id'];
				
				var type = that.getType();
				var tips = is_edit ? lan.database.edit_cloud_server_tips : lan.database.add_cloud_server_tips;

				form['type'] = type;
				
				var layerT = bt.load(tips);
				var interface = is_edit ? 'ModifyCloudServer' : 'AddCloudServer';
				var url = type === 'mysql' ? '/database?action=' + interface : '/database/' + type + '/' + interface;
				bt_tools.send({
					url: url,
					data: type === 'mysql' ? form : { data: JSON.stringify(form) },
				}, function (rdata) {
					layerT.close();
					if (rdata.status) {
						that.reset_server_config();
						layer.close(indexs);
						layer.msg(rdata.msg, { icon: 1 });
					} else {
						layer.msg(rdata.msg, {
							time: 0,
							icon: 2,
							closeBtn: 2,
							shade: 0.3,
							area: '650px',
						});
					}
				});
			},
		});
	},
	// 删除远程服务器管理关系
	del_db_cloud_server: function (row) {
		var that = this;
		bt.confirm(
			{
				title: lan.public.del + ' [' + row.db_host + '] ' + lan.database.cloud_server,
				msg: lan.database.del_cloud_server_tips + '!',
			},
			function () {
				var type = that.getType();
				var params = { url: 'database?action=RemoveCloudServer', data: { id: row.id } }
				if (type != 'mysql') {
					params.url = 'database/' + type + '/RemoveCloudServer';
					params.data = { data: JSON.stringify({ id: row.id }) };
				}
				bt_tools.send(params, function (rdata) {
					if (rdata.status) {

						that.reset_server_config();
					}
					bt.msg(rdata);
				});
			}
		);
	},
	// 重新加载服务
	reset_server_config: function () {
		var type = this.getType();
		$('.database-pos .tabs-item[data-type="' + type + '"]').trigger('click');
	},
	// 删除数据库
	del_database: function (wid, dbname, obj, callback) {
		var that = this;
		var rendom = bt.get_random_code();
		var num1 = rendom['num1'];
		var num2 = rendom['num2'];
		var title = '';
		var tips = 'The deletion may affect the business!';
		title = typeof dbname === 'function' ? 'Batch delete databases' : 'Delete database [ ' + dbname + ' ]';
		if (obj && obj.db_type > 0) {
			tips = lan.database.del_cloud_database_tips;
		}
		layer.open({
			type: 1,
			title: title,
			icon: 0,
			skin: 'delete_site_layer',
			area: '530px',
			closeBtn: 2,
			shadeClose: true,
			content:
				"<div class='bt-form webDelete pd30' id='site_delete_form'>" +
				"<i class='layui-layer-ico layui-layer-ico0'></i>" +
				"<div class='f13 check_title' style='margin-bottom: 20px;'>" + tips + '</div>' +
				"<div style='color:red;margin:18px 0 18px 18px;font-size:14px;font-weight: bold;'>Note: The data is priceless, please operate with caution! ! !" +
				(!recycle_bin_db_open ? '<br><br>Risk: The DB recycle bin is not enabled, deleting will disappear forever!' : '') +
				'</div>' +
				"<div class='vcode'>" + lan.bt.cal_msg +
				"<span class='text'>" + num1 + ' + ' + num2 + "</span>=<input type='number' id='vcodeResult' value=''></div>" +
				'</div>',
			btn: [lan.public.ok, lan.public.cancel],
			yes: function (indexs) {
				var vcodeResult = $('#vcodeResult'),
					data = { id: wid, name: dbname };
				if (vcodeResult.val() === '') {
					layer.tips('Calculation result cannot be empty', vcodeResult, { tips: [1, 'red'], time: 3000 });
					vcodeResult.focus();
					return false;
				} else if (parseInt(vcodeResult.val()) !== num1 + num2) {
					layer.tips('Incorrect calculation result', vcodeResult, { tips: [1, 'red'], time: 3000 });
					vcodeResult.focus();
					return false;
				}
				if (typeof dbname === 'function') {
					delete data.id;
					delete data.name;
				}
				layer.close(indexs);
				var arrs = wid instanceof Array ? wid : [wid];
				var ids = JSON.stringify(arrs),
					countDown = 9;
				if (arrs.length == 1) countDown = 4;
				title = typeof dbname === 'function' ? 'Confirm the information again, delete the database in batches' : 'Confirm the information again, Delete Database [ ' + dbname + ' ]';
				var loadT = bt.load('Checking database data information, please wait...');
				var type = that.getType();
				var params = { url: 'database?action=check_del_data', data: { ids: ids } }
				if (type != 'mysql') {
					params.url = 'database/' + type + '/check_del_data';
					params.data = { data: JSON.stringify({ ids: ids }) };
				}
				bt_tools.send(params, function (res) {
					loadT.close();
					layer.open({
						type: 1,
						title: title,
						closeBtn: 2,
						skin: 'verify_site_layer_info active',
						area: '740px',
						content:
							'<div class="check_delete_site_main pd30">' +
							'<i class="layui-layer-ico layui-layer-ico0"></i>' +
							'<div class="check_layer_title">aaPanel kindly reminds you, please calm down for a few seconds, and then confirm whether you want to delete the data.</div>' +
							'<div class="check_layer_content">' +
							'<div class="check_layer_item">' +
							'<div class="check_layer_site"></div>' +
							'<div class="check_layer_database"></div>' +
							'</div>' +
							'</div>' +
							'<div class="check_layer_error ' +
							(recycle_bin_db_open ? 'hide' : '') +
							'"><span class="glyphicon glyphicon-info-sign"></span>Risk: The database recycle bin is not enabled. After the database is deleted, the database will disappear forever!</div>' +
							'<div class="check_layer_message">Please read the above information to be deleted carefully to prevent the database from being deleted by mistake. Confirm the deletion and there is still <span style="color:red;font-weight: bold;">' +
							countDown +
							'</span> seconds to operate.</div>' +
							'</div>',
						btn: ['Delete (Can be operated after ' + countDown + ' seconds)', 'Cancel'],
						success: function (layers) {
							var html = '',
								rdata = res.data;
							var filterData = rdata.filter(function (el) {
								return ids.indexOf(el.id) != -1;
							});
							for (var i = 0; i < filterData.length; i++) {
								var item = filterData[i],
									newTime = parseInt(new Date().getTime() / 1000),
									t_icon = '<span class="glyphicon glyphicon-info-sign" style="color: red;width:15px;height: 15px;;vertical-align: middle;"></span>';

								database_html = (function (item) {
									var is_time_rule = newTime - item.st_time > 86400 * 30 && item.total > 1024 * 10,
										is_database_rule = res.db_size <= item.total,
										database_time = bt.format_data(item.st_time, 'yyyy-MM-dd'),
										database_size = bt.format_size(item.total);

									var f_size = '<i ' + (is_database_rule ? 'class="warning"' : '') + ' style = "vertical-align: middle;" > ' + database_size + '</i> ' + (is_database_rule ? t_icon : '');
									var t_size = 'Note: This database is large and may be important data. Please operate with caution.\nDatabase: ' + database_size;

									return (
										'<div class="check_layer_database">' +
										'<span title="Database: ' +
										item.name +
										'">Database: ' +
										item.name +
										'</span>' +
										'<span ' +
										(item.total > 0 ? 'title="' + t_size + '"' : '') +
										'>Size: ' +
										f_size +
										'</span>' +
										'<span title="' +
										(is_time_rule && item.total != 0 ? 'Important: This database was created earlier and may be important data. Please operate with caution.' : '') +
										'Time：' +
										database_time +
										'">Ctime：<i ' +
										(is_time_rule && item.total != 0 ? 'class="warning"' : '') +
										'>' +
										database_time +
										'</i></span>' +
										'</div>'
									);
								})(item);
								if (database_html !== '') html += '<div class="check_layer_item">' + database_html + '</div>';
							}
							if (html === '') html = '<div style="text-align: center;width: 100%;height: 100%;line-height: 300px;font-size: 15px;">No data</div>';
							$('.check_layer_content').html(html);
							var interVal = setInterval(function () {
								countDown--;
								$(layers)
									.find('.layui-layer-btn0')
									.text('Delete (Can be operated after ' + countDown + ' seconds)');
								$(layers).find('.check_layer_message span').text(countDown);
							}, 1000);
							setTimeout(function () {
								$(layers).find('.layui-layer-btn0').text('Delete');
								$(layers).find('.check_layer_message').html('<span style="color:red">Note: Please read carefully the above information to be deleted to prevent the database from being deleted by mistake</span>');
								$(layers).removeClass('active');
								clearInterval(interVal);
							}, countDown * 1000);
						},
						yes: function (indes, layers) {
							if ($(layers).hasClass('active')) {
								layer.tips('Please confirm the message, there are ' + countDown + ' seconds left', $(layers).find('.layui-layer-btn0'), { tips: [1, 'red'], time: 3000 });
								return;
							}
							if (typeof dbname === 'function') {
								dbname(data);
							} else {
								bt.database.del_database(data, function (rdata) {
									layer.closeAll();
									if (rdata.status) that.getDatabaseList();
									if (callback) callback(rdata);
									bt.msg(rdata);
								});
							}
						},
					});
				});
			},
		});
	},
	// 同步数据库
	sync_to_database: function (type) {
		var that = this;
		var data = [];
		$('input[type="checkbox"].check:checked').each(function () {
			if (!isNaN($(this).val())) data.push($(this).val());
		});
		console.log(type);
		bt.database.sync_to_database({ type: type, ids: JSON.stringify(data) }, function (rdata) {
			if (rdata.status) that.getDatabaseList();
		});
	},
	// 设置数据库密码
	set_data_pass: function (id, username, password) {
		var that = this;
		var bs = bt.database.set_data_pass(function (rdata) {
			if (rdata.status) that.getDatabaseList();
			bt.msg(rdata);
		});
		$('.name' + bs).val(username);
		$('.id' + bs).val(id);
		$('.password' + bs).val(password);
	},
	// 显示备份列表
	showBackupList: function (id, dbname) {
		var that = this;
		bt.open({
			type: 1,
			skin: 'demo-class',
			area: '700px',
			title: lan.database.backup_title + ' - [' + dbname + ']',
			closeBtn: 2,
			shift: 5,
			shadeClose: false,
			content: '\
			<div class="divtable pd15">\
				<div id="dataBackupList"></div>\
			</div>',
			success: function ($layer) {
				var _that = this;
				_that.$layer = $layer;

				this.renderBackupList();
			},
			// 备份列表
			renderBackupList: function () {
				if (this.backupTable == null) {
					var _that = this;
					this.backupTable = bt_tools.table({
						el: '#dataBackupList',
						url: '/data?action=getData',
						param: { table: 'backup', search: id, type: '1', limit: 8 },
						autoHeight: true,
						load: true,
						default: '[' + dbname + '] The database backup list is empty',
						column: [
							{
								fid: 'name',
								title: lan.database.backup_name,
								width: 220,
								fixed: true,
							},
							{
								fid: 'size',
								title: lan.database.backup_size,
								width: 80,
								type: 'text',
								template: function (row) {
									return bt.format_size(row.size);
								},
							},
							{
								fid: 'addtime',
								width: 150,
								title: lan.database.backup_time,
							},
							{
								fid: 'opt',
								title: lan.database.operation,
								type: 'group',
								width: 150,
								align: 'right',
								group: [
									{
										title: lan.database.backup_re,
										event: function (row) {
											bt.database.input_sql(row.filename, dbname);
										},
									},
									{
										title: lan.database.download,
										template: function (row) {
											return '<a class="btlink" href="/download?filename=' + row.filename + '&amp;name=' + row.name + '" target="_blank">' + lan.database.download + '</a>';
										},
									},
									{
										title: lan.database.del,
										event: function (row) {
											bt.database.del_backup(row.id, function () {
												_that.renderBackupList();
												that.getDatabaseList();
											});
										},
									},
								],
							},
						],
						tootls: [
							{
								type: 'group', // 按钮组
								positon: ['left', 'top'],
								list: [
									{
										title: lan.database.backup,
										active: true,
										event: function (ev) {
											// 备份数据库
											bt.database.backup_data(id, function (rdata) {
												bt.msg(rdata);
												if (rdata.status) {
													_that.renderBackupList();
													that.getDatabaseList();
												}
											});
										},
									},
								],
							},
							{
								type: 'page', // 分页类型
								positon: ['right', 'bottom'], // 默认在右下角
								pageParam: 'p', // 分页请求字段,默认为 : p
								page: 1, // 当前分页 默认：1
								numberParam: 'limit', // 分页数量请求字段默认为 : limit
								defaultNumber: 8, // 分页数量默认 : 20条
							},
						],
						success: function () {
							_that.setLayerCenter();
						},
					});
				} else {
					this.backupTable.$refresh_table_list();
				}
			},
			// 设置弹窗居中
			setLayerCenter: function () {
				var $layer = this.$layer;
				if (!$layer) return;
				var height = $(window).height();
				var layerHeight = $layer.height();
				var top = (height - layerHeight) / 2;
				$layer.css('top', top);
			},
		});
	},
	// 显示导入
	showImport: function (dbname) {
		var that = this;
		var type = this.getType();
		var path = bt.get_cookie('backup_path') + '/database';
		var tips = bt.render_help([lan.database.input_ps1, lan.database.input_ps2, bt.os != 'Linux' ? lan.database.input_ps3.replace(/\/www.*\/database/, path) : lan.database.input_ps3]);
		if (type == 'pgsql') {
			tips = bt.render_help(['Only support sql', bt.os != 'Linux' ? lan.database.input_ps3.replace(/\/www.*\/database/, path) : lan.database.input_ps3]);
		}
		bt.open({
			type: 1,
			shift: 5,
			closeBtn: 2,
			shadeClose: false,
			title: lan.database.input_title_file + '[' + dbname + ']',
			area: ['600px', '500px'],
			content: '<div class="pd15"><div id="dataInputList"></div>' + tips + '</div>',
			success: function () {
				this.renderImportList();
			},
			renderImportList: function () {
				var _that = this;
				if (this.importTable) {
					this.importTable.$refresh_table_list();
				} else {
					var param = { p: 1, reverse: 'True', sort: 'mtime', tojs: 'GetFiles', showRow: 100, path: path };
					this.importTable = bt_tools.table({
						el: '#dataInputList',
						url: '/files?action=GetDir',
						load: true,
						param: param,
						height: 276,
						default: 'No data',
						dataFilter: function (rdata) {
							var data = [];
							for (var i = 0; i < rdata.FILES.length; i++) {
								if (rdata.FILES[i] == null) continue;
								var fmp = rdata.FILES[i].split(';');
								var ext = bt.get_file_ext(fmp[0]);
								if (ext != 'sql' && ext != 'zip' && ext != 'gz' && ext != 'tgz') continue;
								data.push({ name: fmp[0], size: fmp[1], etime: fmp[2] });
							}
							return { data: data };
						},
						column: [
							{
								fid: 'name',
								title: lan.files.file_name,
								width: 190,
								template: function (item) {
									return '<span class="flex" title="' + item.name + '"><span class="text-overflow" style="flex: 1; width: 0;">' + item.name + '</span></span>';
								}
							},
							{
								fid: 'etime',
								title: lan.files.file_etime,
								width: 130,
								type: 'text',
								template: function (item) {
									var time = bt.format_data(item.etime);
									return '<span>' + time + '</span>';
								},
							},
							{
								fid: 'size',
								title: lan.files.file_size,
								width: 70,
								type: 'text',
								template: function (item) {
									return bt.format_size(item.size);
								},
							},
							{
								type: 'group',
								title: 'Operating',
								align: 'right',
								width: 90,
								group: [
									{
										title: lan.database.input,
										event: function (row) {
											var filePath = path + '/' + row.name;
											bt.database.input_sql(filePath, dbname);
										},
									},
									{
										title: 'Del',
										event: function (row) {
											var fileName = path + '/' + row.name;
											layer.confirm(lan.get('recycle_bin_confirm', [fileName]), { title: lan.files.del_file, closeBtn: 2, icon: 3 }, function (index) {
												layer.msg(lan.public.the, { icon: 16, time: 0, shade: [0.3, '#000'] });
												$.post('/files?action=DeleteFile', 'path=' + encodeURIComponent(fileName), function (rdata) {
													layer.close(index);
													bt.msg(rdata);
													if (rdata.status) {
														_that.renderImportList();
													}
												});
											});
										},
									},
								],
							},
						],
						tootls: [
							{
								type: 'group', // 按钮组
								positon: ['left', 'top'],
								list: [
									{
										title: lan.database.input_local_up,
										event: function (ev) {
											// 上传数据库
											var type = that.getType();
											var suffix = type == 'pgsql' ? '.sql' : '.sql,.gz,.tar.gz,.zip';
											bt_upload_file.open(path, suffix, lan.database.input_up_type, function () {
												_that.renderImportList();
											});
										},
									},
								],
							},
						],
					});
				}
			},
		});
	},
};

var mysql = {
	// 数据库表格实例
	databaseTable: null,
	// 获取数据库列表
	getDatabaseList: function (config) {
		if (this.databaseTable) {
			config = config || {};
			if (config.isInit) this.databaseTable.config.page.page = 1;
			this.databaseTable.$refresh_table_list(true);
			return;
		}

		var _that = this;
		var type = database.getType();
		var param = { table: 'databases', search: '' };

		$('#bt_database_table').empty();
		this.databaseTable = bt_tools.table({
			el: '#bt_database_table',
			url: '/data?action=getData',
			param: param, // 参数
			minWidth: '1000px',
			autoHeight: true,
			pageName: 'mysql',
			default: 'The database list is empty', // 数据为空时的默认提示
			beforeRequest: function () {
				var db_type_val = $('.database_type_select_filter').val();
				switch (db_type_val) {
					case 'all':
						delete param['db_type'];
						delete param['sid'];
						break;
					case 0:
						param['db_type'] = 0;
						break;
					default:
						delete param['db_type'];
						param['sid'] = db_type_val;
				}
				return param;
			},
			// 排序
			sortParam: function (data) {
				return {
					order: data.name + ' ' + data.sort,
				};
			},
			column: [
				{ fid: 'id', type: 'checkbox', width: 20 },
				{
					fid: 'name',
					width: 120,
					title: lan.database.add_name,
					template: function (item) {
						return '<span class="limit-text-length" style="width: 100px;" title="' + item.name + '">' + item.name + '</span>';
					},
				},
				{
					fid: 'username',
					width: 120,
					title: lan.database.user,
					sort: function () {
						database_table.$refresh_table_list(true);
					},
					template: function (item) {
						return '<span class="limit-text-length" style="width: 100px;" title="' + item.username + '">' + item.username + '</span>';
					},
				},
				{
					fid: 'password',
					width: 220,
					title: lan.database.add_pass,
					type: 'password',
					copy: true,
					eye_open: true,
					template: function (row) {
						var id = row.id;
						var username = row.username;
						var password = row.password;
						if (row.password === '')
							return '<span span class="c9 cursor" onclick="database.set_data_pass(\'' + id + "','" + username + "','" + password + '\')">' + lan.database.not_found_pwd_1 + '<span class="red">' + lan.database.not_found_pwd_2 + '</span>' + lan.database.not_found_pwd_3 + '!</span>';
						return true;
					},
				},
				bt.public.get_quota_config('database'),
				{
					fid: 'backup',
					title: lan.database.backup,
					width: 130,
					template: function (item) {
						var backup = lan.database.backup_empty;
						var _class = 'bt_warning';
						if (item.backup_count > 0) {
							backup = lan.database.backup_ok;
							_class = 'bt_success';
						}
						var num = item.backup_count > 0 ? '(' + item.backup_count + ')' : '';
						// 备份链接
						var backupLink = '<a href="javascript:;" class="btlink ' + _class + '" onclick="database.showBackupList(' + item.id + ", '" + item.name + '\')">' + backup + num + '</a>';
						// 导入链接
						var importLink = '<a href="javascript:;" class="btlink" onclick="database.showImport(\'' + item.name + '\')">' + lan.database.input + '</a>';
						return '<span>' + backupLink + ' | ' + importLink + '</span>';
					},
				},
				{
					fid: 'position',
					title: lan.database.position,
					type: 'text',
					template: function (row) {
						var type_column = '-';
						var host = row.conn_config.db_host;
						var port = row.conn_config.db_port;
						switch (row.db_type) {
							case 0:
								type_column = lan.database.add_auth_local;
								break;
							case 1:
								type_column = (lan.database.cloud_database + '(' + host + ':' + port + ')').toString();
								break;
							case 2:
								var list = database.cloudDatabaseList;
								$.each(list, function (index, item) {
									var db_host = item.db_host;
									var db_port = item.db_port;
									if (row.sid == item.id) {
										// 默认显示备注
										if (item.ps !== '') {
											type_column = item.ps;
										} else {
											type_column = (lan.database.cloud_database + '(' + db_host + ':' + db_port + ')').toString();
										}
									}
								});
								break;
						}
						return '<span class="flex" title="' + type_column + '"><span class="size_ellipsis">' + type_column + '</span></span>';
					},
				},
				{
					fid: 'ps',
					title: lan.database.add_ps,
					type: 'input',
					blur: function (row, index, ev) {
						bt.pub.set_data_ps(
							{
								id: row.id,
								table: 'databases',
								ps: ev.target.value,
							},
							function (res) {
								layer.msg(res.msg, res.status ? {} : { icon: 2 });
							}
						);
					},
					keyup: function (row, index, ev) {
						if (ev.keyCode === 13) {
							$(this).blur();
						}
					},
				},
				{
					type: 'group',
					title: lan.database.operation,
					width: 280,
					align: 'right',
					group: [
						{
							title: lan.database.admin,
							tips: lan.database.admin_title,
							hide: function (row) {
								return row.db_type != 0;
							},
							event: function (row) {
								bt.database.open_phpmyadmin(row.name, row.username, row.password);
							},
						},
						{
							title: lan.database.auth,
							tips: lan.database.set_db_auth,
							hide: function (row) {
								return row.db_type == 1;
							},
							event: function (row) {
								bt.database.set_data_access(row.username);
							},
						},
						{
							title: lan.database.tools,
							tips: lan.database.mysql_tools,
							event: function (row) {
								_that.rep_tools(row.name);
							},
						},
						{
							title: lan.database.edit_pass,
							tips: lan.database.edit_pass_title,
							hide: function (row) {
								return row.db_type == 1;
							},
							event: function (row) {
								database.set_data_pass(row.id, row.username, row.password);
							},
						},
						{
							title: lan.database.del,
							tips: lan.database.del_title,
							event: function (row) {
								database.del_database(row.id, row.name, row);
							},
						},
					],
				},
			],
			tootls: [
				{
					// 按钮组
					type: 'group',
					positon: ['left', 'top'],
					list: [
						{
							title: lan.database.add_title,
							active: true,
							event: function () {
								database.getCloudServerList(function (list) {
									bt.database.add_database(list, function (res) {
										if (res.status) _that.getDatabaseList();
									});
								});
							},
						},
						{
							title: lan.database.edit_root,
							event: function () {
								bt.database.set_root('root');
							},
						},
						{
							title: 'phpMyAdmin',
							event: function () {
								bt.database.open_phpmyadmin('', 'root', bt.config.mysql_root);
							},
						},
						{
							title: lan.database.cloud_server,
							event: function () {
								database.open_cloud_server();
							},
						},
						{
							title: 'Sync all',
							style: { 'margin-left': '30px' },
							event: function () {
								database.sync_to_database(0);
							},
						},
						{
							title: 'Get DB from server',
							event: function () {
								database.getCloudServerList(function (list) {
									bt_tools.open({
										title: lan.database.select_position,
										area: '450px',
										skin: 'databaseCloudServer',
										btn: [lan.public.confirm, lan.public.cancel],
										content: {
											class: 'pd20',
											form: [
												{
													label: lan.database.position,
													group: {
														type: 'select',
														name: 'sid',
														width: '260px',
														list: list,
													},
												},
											],
										},
										success: function ($layer) {
											$layer.find('.layui-layer-content').css('overflow', 'inherit');
										},
										yes: function (form, index) {
											bt.database.sync_database(form.sid, function (rdata) {
												if (rdata.status) {
													_that.getDatabaseList();
													layer.close(index);
												}
											});
										},
									});
								});
							},
						},
						// {
						// 	title: 'Recycle bin',
						// 	style: {
						// 		'position': 'absolute',
						// 		'right': '-5px'
						// 	},
						// 	icon: 'trash',
						// 	event: function () {
						// 		bt.recycle_bin.open_recycle_bin(6)
						// 	}
						// }
					],
				},
				{
					type: 'batch', // batch_btn
					positon: ['left', 'bottom'],
					placeholder: 'Select batch operation',
					buttonValue: 'Execute',
					disabledSelectValue: 'Select the DB to execute!!',
					selectList: [
						{
							title: 'Sync to Server',
							url: '/database?action=SyncToDatabases&type=1',
							paramName: 'ids', //列表参数名,可以为空
							paramId: 'id', // 需要传入批量的id
							th: 'Database Name',
							refresh: true,
							beforeRequest: function (list) {
								var arry = [];
								$.each(list, function (index, item) {
									arry.push(item.id);
								});
								return JSON.stringify(arry);
							},
							success: function (res, list, that) {
								layer.closeAll();
								var html = '';
								$.each(list, function (index, item) {
									html += '\
									<tr>\
										<td>' + item.name + '</td>\
										<td class="text-right"><span style="color:' + (res.status ? '#20a53a' : 'red') + '">' + res.msg + '</span></td>\
									</tr>';
								});
								that.$batch_success_table({
									title: 'Batch sync selected',
									th: 'Database Name',
									area: '450px',
									html: html,
								});
							},
						},
						{
							title: 'Database Backup',
							url: type == 'mysql' ? 'database?action=ToBackup' : '/database/' + type + '/ToBackup',
							load: true,
							param: function (row) {
								return type == 'mysql' ? { id: row.id } : {data:JSON.stringify({id: row.id})}
							},
							// 手动执行,data参数包含所有选中的站点
							callback: function (that) {
								that.start_batch({}, function (list) {
									var html = '';
									for(var i=0;i<list.length;i++){
										var item = list[i];
										html += '<tr><td>'+ item.name +'</td><td><div style="float:right;"><span style="color:'+ (item.request.status?'#20a53a':'red') +'">'+ item.request.msg +'</span></div></td></tr>';
									}
									_that.databaseTable.$batch_success_table({
										title: 'Batch backup database',
										th: 'Database Name',
										html: html,
										area: '480px',
									});
									_that.getDatabaseList();
								});
							}
						},
						{
							title: 'Delete database',
							url: '/database?action=DeleteDatabase',
							load: true,
							refresh: true,
							param: function (row) {
								return {
									id: row.id,
									name: row.name,
								};
							},
							callback: function (that) {
								// 手动执行, data参数包含所有选中的站点
								var ids = [];
								for (var i = 0; i < that.check_list.length; i++) {
									ids.push(that.check_list[i].id);
								}
								database.del_database(ids, function (param) {
									that.start_batch(param, function (list) {
										layer.closeAll();
										var html = '';
										for (var i = 0; i < list.length; i++) {
											var item = list[i];
											html += '\
											<tr>\
												<td>' + item.name + '</td>\
												<td class="text-right">\
													<span style="color:' + (item.request.status ? '#20a53a' : 'red') + '">' + item.request.msg + '</span>\
												</td>\
											</tr>';
										}
										_that.databaseTable.$batch_success_table({
											title: 'Batch deletion',
											th: 'Database Name',
											html: html,
										});
										_that.getDatabaseList();
									});
								});
							},
						},
					],
				},
				{
					type: 'search',
					positon: ['right', 'top'],
					placeholder: lan.database.database_search,
					searchParam: 'search', // 搜索请求字段，默认为 search
					value: '', // 当前内容,默认为空
				},
				{
					type: 'page', // 分页显示
					positon: ['right', 'bottom'], // 默认在右下角
					pageParam: 'p', //分页请求字段,默认为 : p
					page: 1, //当前分页 默认：1
					numberParam: 'limit', //分页数量请求字段默认为 : limit
					number: 20, //分页数量默认 : 20条
					numberList: [10, 20, 50, 100, 200], // 分页显示数量列表
					numberStatus: true, //　是否支持分页数量选择,默认禁用
					jump: true, //是否支持跳转分页,默认禁用
				},
			],
success: function () {
			$('.feedback-btn').remove();
			$('.tootls_group.tootls_top .pull-left').append('<span style="display:inline-block; margin-left:10px;vertical-align: bottom;" class="feedback-btn"><span class="flex" style="align-items: center;margin-right:16px;width:100px;"><i class="icon-demand"></i><a class="btlink" onClick="javascript:bt.openFeedback({title:\'aaPanel demand feedback collection\',placeholder:\'<span>If you encounter any problems or imperfect functions during use, please describe <br> your problems or needs to us in detail, we will try our best to solve or improve for <br> you</span>\',recover:\'We pay special attention to your requirements feedback, and we conduct regular weekly requirements reviews. I hope I can help you better\',key:993,proType:2});" style="margin-left: 5px;">Feedback</a></span></span>');
					
			}
		});
		database.renderCloudServerSelect();
	},
	// 数据库工具
	rep_tools: function (db_name) {
		var that = this;
		layer.open({
			type: 1,
			title: lan.database.mysql_tools_box + ' [ ' + db_name + ' ]',
			area: ['870px', '590px'],
			closeBtn: 2,
			shadeClose: false,
			content:
				'\
			<div class="pd15">\
				<div class="db_tools_info">\
					<div class="info">\
						<div class="name">' + lan.database.db_name + ': <span>--</span></div>\
						<div class="size">' + lan.database.size + ': <span>0 B</span></div>\
					</div>\
					<div class="hide" id="db_tools"></div>\
				</div>\
				<div id="databaseToolsTable"></div>\
			</div>',
			success: function (layero, index) {
				var _that = this;
				var tips = '<ul class="help-info-text c7">\
					<li>' + lan.database.tb_repair + '</li>\
					<li>' + lan.database.tb_optimization + '</li>\
					<li>' + lan.database.tb_change_engine + '</li>\
				</ul>';
				$('#databaseToolsTable').after(tips);
				var repair = '<button class="btn btn-default btn-sm btn-tools-repair">' + lan.database.repair + '</button>';
				var optimization = '<button class="btn btn-default btn-sm btn-tools-opt">' + lan.database.optimization + '</button>';
				var innoDB = '<button class="btn btn-default btn-sm btn-tools-innodb">' + lan.database.change + 'InnoDB</button>';
				var myisam = '<button class="btn btn-default btn-sm btn-tools-myisam">' + lan.database.change + 'MyISAM</button>';
				$('#db_tools').html(repair + optimization + innoDB + myisam);

				// 修复
				$('#db_tools').on('click', '.btn-tools-repair', function () {
					_that.rep_database(db_name);
				});

				// 优化
				$('#db_tools').on('click', '.btn-tools-opt', function () {
					_that.op_database(db_name);
				});

				// 转成innoDb
				$('#db_tools').on('click', '.btn-tools-innodb', function () {
					_that.to_database_type(db_name, null, 'InnoDB');
				});

				// 转成MyISAM
				$('#db_tools').on('click', '.btn-tools-myisam', function () {
					_that.to_database_type(db_name, null, 'MyISAM');
				});

				this.getTable();
			},
			getTable: function () {
				$('#db_tools').addClass('hide');
				if (this.table) {
					this.table.$refresh_table_list();
					return;
				}
				var _that = this;
				var types = { InnoDB: 'InnoDB', MyISAM: 'MyISAM' };
				this.table = bt_tools.table({
					el: '#databaseToolsTable',
					url: '/database?action=GetInfo',
					param: { db_name: db_name },
					height: '355px',
					autoHeight: true,
					dataFilter: function (res) {
						$('.db_tools_info .name span').text(res.database);
						$('.db_tools_info .name span').attr('title', res.database);
						$('.db_tools_info .size span').text(res.data_size);
						return { data: res.tables };
					},
					handleSelectionChange: function (row, list, ev) {
						if (list.length) {
							$('#db_tools').removeClass('hide');
						} else {
							$('#db_tools').addClass('hide');
						}
					},
					column: [
						{
							type: 'checkbox',
							width: 20,
						},
						{
							fid: 'table_name',
							title: lan.database.tb_name,
							type: 'text',
							width: 170,
							template: function (row) {
								return '<span class="flex"><span class="text-overflow" title="' + row.table_name + '">' + row.table_name + '</span></span>';
							},
						},
						{
							fid: 'type',
							title: lan.database.engine,
						},
						{
							fid: 'collation',
							title: lan.database.character,
							type: 'text',
							width: 130,
							template: function (item) {
								return '<span class="flex"><span class="text-overflow" title="' + item.collation + '">' + item.collation + '</span></span>';
							},
						},
						{
							fid: 'rows_count',
							title: lan.database.row_num,
							width: 100,
						},
						{
							fid: 'data_size',
							title: lan.database.size,
						},
						{
							type: 'group',
							align: 'right',
							title: lan.database.operation,
							width: 250,
							group: [
								{
									title: lan.database.backup_re,
									event: function (row) {
										_that.rep_database(db_name, row.table_name);
									},
								},
								{
									title: lan.database.optimization,
									event: function (row) {
										_that.op_database(db_name, row.table_name);
									},
								},
								{
									template: function (row) {
										var setType = row.type == 'InnoDB' ? types.MyISAM : types.InnoDB;
										return lan.database.change + setType;
									},
									event: function (row) {
										var setType = row.type == 'InnoDB' ? types.MyISAM : types.InnoDB;
										_that.to_database_type(db_name, row.table_name, setType);
									},
								},
							],
						},
					],
				});

			    $('#databaseToolsTable').on('change', '.cust—checkbox-input', function () {
			        var isChecked = false;
			        var elems = $('#databaseToolsTable tbody .cust—checkbox');
			        for (var i = 0; i < elems.length; i++) {
			            if ($(elems[i]).hasClass('active')) {
			                isChecked = true;
			                break;
			            }
			        }
			        if (isChecked) {
			            $('#db_tools').removeClass('hide');
			        } else {
			            $('#db_tools').addClass('hide');
			        }
			    });
			},
			// 修复表
			rep_database: function (db_name, tables) {
				var _that = this;
				var dbs = this.rep_checkeds(tables);
				var loadT = layer.msg(lan.database.send_repair_command, { icon: 16, time: 0 });
				bt.send('ReTable', 'database/ReTable', { db_name: db_name, tables: JSON.stringify(dbs) }, function (rdata) {
					layer.close(loadT);
					bt.msg(rdata);
					if (rdata.status) _that.getTable();
				});
			},
			// 优化表
			op_database: function (db_name, tables) {
				var _that = this;
				var dbs = this.rep_checkeds(tables);
				var loadT = layer.msg(lan.database.send_opt_command, { icon: 16, time: 0 });
				bt.send('OpTable', 'database/OpTable', { db_name: db_name, tables: JSON.stringify(dbs) }, function (rdata) {
					layer.close(loadT);
					bt.msg(rdata);
					if (rdata.status) _that.getTable();
				});
			},
			// 转换表类型
			to_database_type: function (db_name, tables, type) {
				var _that = this;
				var dbs = this.rep_checkeds(tables);
				var loadT = layer.msg(lan.database.send_change_command, { icon: 16, time: 0, shade: [0.3, '#000'] });
				bt.send('AlTable', 'database/AlTable', { db_name: db_name, tables: JSON.stringify(dbs), table_type: type }, function (rdata) {
					layer.close(loadT);
					bt.msg(rdata);
					if (rdata.status) _that.getTable();
				});
			},
			rep_checkeds: function (tables) {
				var dbs = [];
				if (tables) {
					dbs.push(tables);
				} else {
					var table = this.table;
					if (table) {
						$.each(table.checkbox_list, function (index, item) {
							var row = table.data[item];
							dbs.push(row.table_name);
						});
					}
				}
				if (dbs.length < 1) {
					layer.msg(lan.database.choose_at_least_one_tb, { icon: 2 });
					return false;
				}
				return dbs;
			},
		});
	},
}

var sqlserver = {
	// 服务器列表
	databaseTable: null,
	// 渲染数据库列表
	getDatabaseList: function (config) {
		if (this.databaseTable) {
			config = config || {};
			if (config.isInit) this.databaseTable.config.page.page = 1;
			this.databaseTable.$refresh_table_list(true);
			return
		}
		var _that = this;
		var type = database.getType();
		var param = { table: 'databases', search: '' }
		this.databaseTable = bt_tools.table({
			el: '#bt_sqldatabase_table',
			url: 'database/sqlserver/get_list',
			param: param, //参数
			minWidth: '1000px',
			load: true,
			autoHeight: true,
			default: "The database list is empty", // 数据为空时的默认提示
			pageName: 'database',
			beforeRequest:function(beforeData){
				var db_type_val = $('.sqlserver_type_select_filter').val()
				switch(db_type_val){
					case 'all':
						delete param['db_type']
						delete param['sid']
						break;
					case 0:
						param['db_type'] = 0;
						break;
					default:
						delete param['db_type'];
						param['sid'] = db_type_val
				}
				if (beforeData.hasOwnProperty('data') && typeof beforeData.data === 'string') {
					delete beforeData['data']
					return { data: JSON.stringify($.extend(param,beforeData)) }
				}
				return {data:JSON.stringify(param)}
			},
			column:[
				{type: 'checkbox',width: 20},
				{fid: 'name', title: lan.database.add_name,type:'text'},
				{fid: 'username',title: lan.database.user,type:'text',sort:true},
				{fid:'password',title: lan.database.add_pass,type:'password',copy:true,eye_open:true},
				{
					title: lan.database.position,
					type: 'text',
					width: 116,
					template: function (row) {
						var type_column = '-'
						switch(row.db_type){
							case 0:
								type_column = lan.database.add_auth_local
								break;
							case 1:
								type_column = (lan.database.cloud_database + '('+row.conn_config.db_host+':'+row.conn_config.db_port+')').toString()
								break;
							case 2:
								var list = database.cloudDatabaseList;
								$.each(list,function(index,item){
									if(row.sid == item.id){
										if(item.ps !== ''){ // 默认显示备注
											type_column = item.ps
										}else{
											type_column = (lan.database.cloud_database  + '('+item.db_host+':'+item.db_port+')').toString()
										}
									}
								})
								break;
						}
						return '<span class="flex" style="width:100px" title="'+type_column+'"><span class="size_ellipsis" style="width: 0; flex: 1;">'+type_column+'</span></span>'
					}
				},
				{
					fid: 'ps',
					title: lan.database.add_ps,
					type: 'input',
					blur: function (row, index, ev) {
						bt.pub.set_data_ps({
							id: row.id,
							table: 'databases',
							ps: ev.target.value
						}, function (res) {
							layer.msg(res.msg, (res.status ? {} : {
								icon: 2
							}));
						});
					},
					keyup: function (row, index, ev) {
						if (ev.keyCode === 13) {
							$(this).blur();
						}
					}
				},
				{
					type: 'group',
					title: lan.database.operation,
					width: 220,
					align: 'right',
					group: [
						{
							title: lan.database.edit_pass,
							tips: lan.database.edit_pass_title,
							hide: function (rows) {
								return rows.db_type == 1
							},
							event: function (row) {
								database.set_data_pass(row.id, row.username, row.password);
							}
						},
						{
							title: lan.database.del,
							tips: lan.database.del_title,
							event: function (row) {
								database.del_database(row.id, row.name, row);
							}
						}
					]
				}
			],
			sortParam: function (data) {
				return {
					'order': data.name + ' ' + data.sort
				};
			},
			tootls: [{ // 按钮组
				type: 'group',
				positon: ['left', 'top'],
				list: [{
					title: lan.database.add_title,
					active: true,
					event: function () {
						database.getCloudServerList(function (list) {
							bt.database.add_database(list, function (res) {
								if (res.status) _that.getDatabaseList();
							})
						});
					}
				},{
					title: lan.database.cloud_server,
					event:function(){
						database.open_cloud_server();
					}
				},{
					title: 'Sync all',
					style:{'margin-left':'30px'},
					event: function () {
						bt.database.sync_to_database({ type:0, ids: [] }, function (res) {
							if (res.status) _that.getDatabaseList();
						})
					}
				},{
					title: 'Get DB from server',
					event: function () {
						database.getCloudServerList(function (list) {
							bt_tools.open({
								title: lan.database.select_position,
								area: '450px',
								btn: [lan.public.confirm, lan.public.cancel],
								skin: 'databaseCloudServer',
								content: {
									'class':'pd20',
									form:[{
										label: lan.database.position,
										group:{
											type: 'select',
											name: 'sid',
											width: '260px',
											list: list
										}
									}]
								},
								success: function (layers) {
									$(layers).find('.layui-layer-content').css('overflow','inherit');
								},
								yes:function (form, layers, index){
									bt.database.sync_database(form.sid, function (rdata) {
										if (rdata.status){
											_that.getDatabaseList();
											layer.close(layers)
										}
									});
								}
							});
						});
					}
				}]
			},{
				type: 'batch', // batch_btn
				positon: ['left', 'bottom'],
				placeholder: 'Select batch operation',
				buttonValue: 'Execute',
				disabledSelectValue: 'Select the DB to execute!!',
				selectList: [{
					title: 'Sync to Server',
					url: '/database/' + type + '/SyncToDatabases',
					paramName: 'data', //列表参数名,可以为空
					th: 'Database Name',
					beforeRequest: function(list) {
						var arry = [];
						$.each(list, function (index, item) {
							arry.push(item.id);
						});
						return JSON.stringify({ids:JSON.stringify(arry),type:1})
					},
					success: function (res, list, that) {
						layer.closeAll();
						var html = '';
						$.each(list, function (index, item) {
							html += '\
							<tr>\
								<td>' + item.name + '</td>\
								<td class="text-right"><span style="color:' + (res.status ? '#20a53a' : 'red') + '">' + res.msg + '</span></td>\
							</tr>';
						});
						that.$batch_success_table({
							title: 'Batch sync selected',
							th: 'Database Name',
							area: '450px',
							html: html
						});
					}
				},{
					title: 'Delete database',
					url: '/database/' + type + '/DeleteDatabase',
					load: true,
					param: function (row) {
						return {
							data: JSON.stringify({ id: row.id, name: row.name })
						}
					},
					callback: function (that) { // 手动执行,data参数包含所有选中的站点
						var ids = [];
						for (var i = 0; i < that.check_list.length; i++) {
							ids.push(that.check_list[i].id);
						}
						database.del_database(ids,function(param){
							that.start_batch(param, function (list) {
								layer.closeAll()
								var html = '';
								for (var i = 0; i < list.length; i++) {
									var item = list[i];
									html += '\
									<tr>\
										<td>' + item.name + '</td>\
										<td class="text-right">\
											<span style="color:' + (item.request.status ? '#20a53a' : 'red') + '">' + item.request.msg + '</span>\
										</td>\
									</tr>';
								}
								_that.databaseTable.$batch_success_table({
									title: 'Batch deletion',
									th: 'Database Name',
									html: html
								});
								_that.getDatabaseList();
							});
						})
					}
				}]
			}, {
				type: 'search',
				positon: ['right', 'top'],
				placeholder: lan.database.database_search,
				searchParam: 'search', //搜索请求字段，默认为 search
				value: '',// 当前内容,默认为空
			}, { //分页显示
				type: 'page',
				positon: ['right', 'bottom'], // 默认在右下角
				pageParam: 'p', //分页请求字段,默认为 : p
				page: 1, //当前分页 默认：1
				numberParam: 'limit', //分页数量请求字段默认为 : limit
				number: 20, //分页数量默认 : 20条
				numberList: [10, 20, 50, 100, 200], // 分页显示数量列表
				numberStatus: true, //　是否支持分页数量选择,默认禁用
				jump: true, //是否支持跳转分页,默认禁用
			}],
		});
		database.renderCloudServerSelect();
	}
}

var mongodb = {
	// 数据库表格实例
	databaseTable: null,
	// 是否开启安全认证
	mongoDBAccessStatus: false,
	// 获取数据库列表
  getDatabaseList :function() {
		if (this.databaseTable) {
			this.databaseTable.$refresh_table_list(true);
			return;
		}

		var _that = this;
		var type = database.getType();
    var param = { table: 'databases', search: '' }

    $('#bt_mongodb_table').empty();
    this.databaseTable = bt_tools.table({
      el: '#bt_mongodb_table',
      url: 'database/' + type + '/get_list',
      param: param, //参数
      minWidth: '1000px',
      load: true,
      autoHeight: true,
      default: 'The database list is empty', // 数据为空时的默认提示
      pageName: 'database',
      beforeRequest:function(beforeData){
        var db_type_val = $('input[name="db_type_filter_' + type + '"]').val();
        switch(db_type_val){
          case 'all':
            delete param['db_type']
            delete param['sid']
            break;
          case 0:
            param['db_type'] = 0;
            break;
          default:
            delete param['db_type'];
            param['sid'] = db_type_val
        }
        if (beforeData.hasOwnProperty('data') && typeof beforeData.data === 'string') {
          delete beforeData['data']
          return { data: JSON.stringify($.extend(param,beforeData)) }
        }
        return {data:JSON.stringify(param)}
      },
			sortParam: function (data) {
        return {
          'order': data.name + ' ' + data.sort
        };
      },
      column:[
        {
					type: 'checkbox',
					width: 20
				},
        {
					fid: 'name',
					title: lan.database.add_name,
					type:'text'
				},
        {
					fid: 'username',
					title: lan.database.user,
					type:'text',
					sort: true
				},
        {
					fid: 'password',
					title: lan.database.add_pass,
					type:'password',
					copy:true,
					eye_open:true
				},
        {
          fid:'backup',
          title: lan.database.backup,
          width: 130,
          template: function (item) {
            var backup = lan.database.backup_empty;
            var _class = "bt_warning";
            if (item.backup_count > 0) {
							backup = lan.database.backup_ok;
							_class = 'bt_success';
						}
						var num = item.backup_count > 0 ? '(' + item.backup_count + ')' : '';
						// 备份链接
						var backupLink = '<a href="javascript:;" class="btlink ' + _class + '" onclick="database.showBackupList(' + item.id + ", '" + item.name + '\')">' + backup + num + '</a>';
						// 导入链接
						var importLink = '<a href="javascript:;" class="btlink" onclick="database.showImport(\'' + item.name + '\')">' + lan.database.input + '</a>';
						return '<span>' + backupLink + ' | ' + importLink + '</span>';
          }
        },
        {
					fid: 'position',
          title: lan.database.position,
          type: 'text',
          width: 120,
          template: function (row) {
            var type_column = '-';
						var host = row.conn_config.db_host;
						var port = row.conn_config.db_port;
            switch(row.db_type){
              case 0:
                type_column = lan.database.add_auth_local;
                break;
              case 1:
                type_column = (lan.database.cloud_database + '(' + host + ':' + port + ')').toString();
                break;
              case 2:
								var list = database.cloudDatabaseList;
                $.each(list, function(index, item) {
									var db_host = item.db_host;
									var db_port = item.db_port;
                  if (row.sid == item.id) {
										// 默认显示备注
                    if (item.ps !== '') {
                      type_column = item.ps
                    } else {
                      type_column = (lan.database.cloud_database + '(' + db_host + ':' + db_port + ')').toString();
                    }
                  }
                })
                break;
            }
            return '<span class="flex" title="' + type_column + '"><span class="text-overflow">' + type_column + '</span></span>';
          }
        },
        {
          fid: 'ps',
          title: lan.database.add_ps,
          type: 'input',
          blur: function (row, index, ev) {
            bt.pub.set_data_ps({
              id: row.id,
              table: 'databases',
              ps: ev.target.value
            }, function (res) {
              layer.msg(res.msg, (res.status ? {} : {
                icon: 2
              }));
            });
          },
          keyup: function (row, index, ev) {
            if (ev.keyCode === 13) {
              $(this).blur();
            }
          }
        },
        {
          type: 'group',
          title: lan.database.operation,
          width: 220,
          align: 'right',
          group: [{
            title: lan.database.edit_pass,
            tips: lan.database.edit_pass_title,
            hide:function(rows){return rows.db_type == 1},
            event: function (row) {
              database.set_data_pass(row.id, row.username, row.password);
            }
          }, {
            title: lan.database.del,
            tips: lan.database.del_title,
            event: function (row) {
              database.del_database(row.id, row.name, row);
            }
          }]
        }
      ],
      tootls: [{ // 按钮组
        type: 'group',
        positon: ['left', 'top'],
        list: [
					{
						title: lan.database.add_title,
						active: true,
						event: function () {
							database.getCloudServerList(function (list) {
								bt.database.add_database(list, function (res) {
									if (res.status) _that.getDatabaseList();
								});
							});
						}
					},
					{
						title: lan.database.edit_root,
						event: function (ev) {
							if (_that.mongoDBAccessStatus) {
								bt.database.set_root('mongo');
							} else {
								$(ev.currentTarget).next().click();
								layer.msg(lan.database.safety_auth_warn1, { icon: 0 });
							}
						}
					},
					{
						title: lan.database.safety_auth,
						event: function () {
							layer.open({
								type: 1,
								closeBtn: 2,
								shift: 5,
								shadeClose: false,
								title: lan.database.safety_auth,
								area: '400px',
								btn: false,
								content:'\
								<div class="bt-form pd20">\
									<div class="line">\
										<span class="tname" style="width: 160px;">' + lan.database.safety_auth + '</span>\
										<div class="info-r" style="margin-left: 160px;">\
											<div class="inlineBlock mr50" style="margin-top: 5px;vertical-align: -6px;">\
												<input class="btswitch btswitch-ios" id="mongodb_access" type="checkbox" name="monitor">\
												<label class="btswitch-btn" for="mongodb_access" style="margin-bottom: 0;"></label>\
											</div>\
										</div>\
									</div>\
									<ul class="help-info-text c7" style="margin-top: 8px;">\
										<li>' + lan.database.safety_auth_tips1 + '</li>\
									</ul>\
								</div>',
								success:function(){
									var status = _that.mongoDBAccessStatus
									$('#mongodb_access').attr('checked', status)

									$('#mongodb_access').click(function(){
										var _status = $(this).prop('checked')
										bt_tools.send({
											url: 'database/' + type + '/set_auth_status',
											data:{ data: JSON.stringify({ status: _status ? 1 : 0 })},
											verify: true
										}, function (rdata) {
											if (rdata.status) {
												_that.mongoDBAccessStatus = _status
												layer.msg(rdata.msg, { icon: 1 });
											}
										}, lan.database.safety_auth_req1)
									})
								}
							})
						}
					},
					{
						title: lan.database.cloud_server,
						event:function(){
							database.open_cloud_server();
						}
					},
					{
						title: 'Sync all',
						style:{'margin-left':'30px'},
						event: function () {
							bt.database.sync_to_database({type:0,data:[]},function(res){
								if(res.status) _that.getDatabaseList();
							})
						}
					},
					{
						title: 'Get DB from server',
						event: function () {
							database.getCloudServerList(function (list) {
								bt_tools.open({
									title: lan.database.select_position,
									area: '450px',
									btn: [lan.public.confirm, lan.public.cancel],
									skin: 'databaseCloudServer',
									content: {
										'class':'pd20',
										form:[{
											label: lan.database.position,
											group:{
												type: 'select',
												name: 'sid',
												width: '260px',
												list: list
											}
										}]
									},
									success: function (layers) {
										$(layers).find('.layui-layer-content').css('overflow','inherit');
									},
									yes:function (form, layers, index){
										bt.database.sync_database(form.sid, function (rdata) {
											if (rdata.status){
												_that.getDatabaseList();
												layer.close(layers)
											}
										});
									}
								});
							});
						}
					}
				]
      },
			{
        type: 'batch', //batch_btn
        positon: ['left', 'bottom'],
        placeholder: 'Select batch operation',
				buttonValue: 'Execute',
				disabledSelectValue: 'Select the DB to execute!!',
        selectList: [
					{
						title: 'Sync to Server',
						url: '/database/' + type + '/SyncToDatabases',
						paramName: 'data', //列表参数名,可以为空
						th: 'Database Name',
						beforeRequest: function(list) {
							var arry = [];
							$.each(list, function (index, item) {
								arry.push(item.id);
							});
							return JSON.stringify({ids:JSON.stringify(arry),type:1})
						},
						success: function (res, list, that) {
							layer.closeAll();
							var html = '';
							$.each(list, function (index, item) {
								html += '\
								<tr>\
									<td>' + item.name + '</td>\
									<td class="text-right"><span style="color:' + (res.status ? '#20a53a' : 'red') + '">' + res.msg + '</span></td>\
								</tr>';
							});
							that.$batch_success_table({
								title: 'Batch sync selected',
								th: 'Database Name',
								area: '450px',
								html: html
							});
						}
					},
					{
						title: 'Database Backup',
						url: type == 'mysql' ? 'database?action=ToBackup' : '/database/' + type + '/ToBackup',
						load: true,
						param: function (row) {
							return type == 'mysql' ? { id: row.id } : {data:JSON.stringify({id: row.id})}
						},
						// 手动执行,data参数包含所有选中的站点
						callback: function (that) {
							that.start_batch({}, function (list) {
								var html = '';
								for(var i=0;i<list.length;i++){
									var item = list[i];
									html += '<tr><td>'+ item.name +'</td><td><div style="float:right;"><span style="color:'+ (item.request.status?'#20a53a':'red') +'">'+ item.request.msg +'</span></div></td></tr>';
								}
								_that.databaseTable.$batch_success_table({
									title: 'Batch backup database',
									th: 'Database Name',
									html: html,
									area: '480px',
								});
								_that.getDatabaseList();
							});
						}
					},
					{
						title: 'Delete database',
						url: '/database/' + type + '/DeleteDatabase',
						load: true,
						param: function (row) {
							return {
								data: JSON.stringify({ id: row.id, name: row.name })
							}
						},
						callback: function (that) { // 手动执行,data参数包含所有选中的站点
							var ids = [];
							for (var i = 0; i < that.check_list.length; i++) {
								ids.push(that.check_list[i].id);
							}
							database.del_database(ids,function(param){
								that.start_batch(param, function (list) {
									layer.closeAll()
									var html = '';
									for (var i = 0; i < list.length; i++) {
										var item = list[i];
										html += '\
										<tr>\
											<td>' + item.name + '</td>\
											<td class="text-right">\
												<span style="color:' + (item.request.status ? '#20a53a' : 'red') + '">' + item.request.msg + '</span>\
											</td>\
										</tr>';
									}
									_that.databaseTable.$batch_success_table({
										title: 'Batch deletion',
										th: 'Database Name',
										html: html
									});
									_that.getDatabaseList();
								});
							})
						}
					}]
				},
				{
					type: 'search',
					positon: ['right', 'top'],
					placeholder: lan.database.database_search,
					searchParam: 'search', //搜索请求字段，默认为 search
					value: '',// 当前内容,默认为空
				},
				{ 
					type: 'page', // 分页显示
					positon: ['right', 'bottom'], // 默认在右下角
					pageParam: 'p', //分页请求字段,默认为 : p
					page: 1, //当前分页 默认：1
					numberParam: 'limit', //分页数量请求字段默认为 : limit
					number: 20, //分页数量默认 : 20条
					numberList: [10, 20, 50, 100, 200], // 分页显示数量列表
					numberStatus: true, //　是否支持分页数量选择,默认禁用
					jump: true, //是否支持跳转分页,默认禁用
				}
			]
    });

		database.renderCloudServerSelect();
  }
}

var redis = {
	// 数据库表格实例
	databaseTable: null,
  redisDBList: [],
	// 当前远程信息
  cloudInfo: {
    sid: 0,
    title: 'local server'
  },
	event: function () {
		var that = this;
		// 添加Key
		$('.addRedisDB').click(function () {
			that.set_redis_library();
		});
		// 远程服务器
		$('.RedisCloudDB').click(function () {
			database.open_cloud_server();
		});
		// 备份
		$('.backupRedis').click(function () {
			that.backup_redis_list()
		});
		// 清空所有
		$('.emptyRedisDB').click(function () {
			that.choose_redis_list();
		});
		// 远程服务器列表点击事件
    $('#bt_redis_view').on('change', '.redis_type_select_filter', function(){
      that.cloudInfo.sid = $(this).val();
      that.cloudInfo.title = $(this).find('option:selected').text();
      that.render_redis_content();
    });
	},
  getDatabaseList: function () {
    var that = this;
    this.cloudInfo.sid = database.cloudDatabaseList.length == 0 ? 0 : database.cloudDatabaseList[0].id
    this.cloudInfo.title = database.cloudDatabaseList.length == 0 ? 'local server' : database.cloudDatabaseList[0].ps

    // 远程服务器列表
    that.renderServerSelect();

    // 渲染redis列表
    this.render_redis_content()
  },
	// 渲染redis选择器
	renderServerSelect: function () {
		var _option = '';
		$.each(database.cloudDatabaseList, function (index, item) {
			var _tips = item.ps != '' ? item.ps : item.db_host;
			_option += '<option value="' + item.id + '">' + _tips + '</option>';
		});
		if ($('#bt_redis_view .tool_list_right .redis_type_select_filter').length === 0) {
			$('#bt_redis_view .tool_list_right').append('<select class="bt-input-text mr5 redis_type_select_filter" style="width:110px" name="db_type_filter">' + _option + '</select>');
		} else {
			$('#bt_redis_view .tool_list_right .redis_type_select_filter').html(_option);
		}
	},
	// 渲染redis列表
  render_redis_content: function (id) {
    var that = this;
    $('#redis_content_tab').remove();
    $('#bt_redis_view').append('\
		<div id="redis_content_tab">\
			<div class="tab-nav"></div>\
			<div class="tab-con redis_table_content" style="padding:10px 0"></div>\
		</div>');
    var tabHTML = '';

    bt_tools.send({ url: 'database/redis/get_list', data: { data: JSON.stringify({ sid: that.cloudInfo.sid }) } }, function (rdata) {
			that.redisDBList = rdata;
			$.each(rdata, function (index, item) {
				tabHTML += '<span data-id="' + item.id + '">' + item.name + '(' + item.keynum + ')</span>';
			});
			$('#redis_content_tab .tab-nav').html(tabHTML);
		
			setTimeout(function () {
				if (id) {
					$('#redis_content_tab .tab-nav span:contains(DB' + id + ')').click();
				} else {
					if (rdata.length == 0) {
						$('#redis_content_tab .tab-nav').remove();
						that.render_redis_table(0);
					} else {
						$('#redis_content_tab .tab-nav span:eq(0)').click();
					}
				}
			}, 50);
		
			// redis数据库点击事件
			$('#redis_content_tab .tab-nav span').click(function () {
				var _id = $(this).data('id');
				$(this).addClass('on').siblings().removeClass('on');
				that.render_redis_table(_id);
			});
		});
  },
  render_redis_table: function (id) {
		if (this.databaseTable && id == undefined) {
			this.databaseTable.$refresh_table_list(true);
			return;
		}

    var that = this;
    $('.redis_table_content').empty();
    this.databaseTable = bt_tools.table({
      el: '.redis_table_content',
      url: 'database/redis/get_db_keylist',
      param: { db_idx: id }, //参数
      minWidth: '1000px',
      autoHeight: true,
      load: true,
      default: 'The database list is empty', // 数据为空时的默认提示
      pageName: 'database',
      beforeRequest:function(beforeData){
        var db_type_val = that.cloudInfo.sid;
				var param = {};
				switch (db_type_val) {
					case 0:
						param['db_type'] = 0;
						break;
					default:
						delete param['db_type'];
						param['sid'] = db_type_val;
				}
				if (beforeData.hasOwnProperty('data') && typeof beforeData.data === 'string') {
					delete beforeData['data'];
					return { data: JSON.stringify($.extend(param, { db_idx: id }, beforeData)) };
				}
				return { data: JSON.stringify($.extend(param, { db_idx: id, limit: beforeData.limit })) };
      },
      column:[
				{ type: 'checkbox', width: 20 },
				{ fid: 'name', title: lan.public_backup.key },
        {
					fid: 'val',
					title: lan.public_backup.value,
					type:'text',
					template: function (row) {
            var _val = $('<div></div>').text(row.val)
            return '<div class="flex" style="width: 350px;" title="'+_val.text().replace(/\"/g, '\&quot;')+'"><span class="text-overflow">'+_val.text()+'</span><span class="ico-copy cursor btcopy ml5" title="' + lan.mail_sys.copy + '"></span></div>';
          },
					event: function(row,index,ev,key){
            if($(ev.target).hasClass('btcopy')){
              bt.pub.copy_pass(row.val.replaceAll("&quot;", "\""));
            }
          }
				},
        { fid: 'type', title: lan.database.data_type },
				{ fid: 'len', title: lan.database.data_len },
        {
					fid: 'endtime',
					title: lan.database.term_of_validity,
					type: 'text',
					template: function (row) {
						return that.reset_time_format(row.endtime);
					},
				},
        {
					type: 'group',
					title: lan.database.operation,
					width: 220,
					align: 'right',
					group: [
						{
							title: lan.public.edit,
							tips: lan.database.edit_data,
							hide: function (rows) {
								return rows.type == 'string' || rows.type == 'int' ? false : true;
							},
							event: function (row) {
								row.db_idx = id;
								that.set_redis_library(row);
							},
						},
						{
							title: lan.public.del,
							tips: lan.database.del_data,
							event: function (row) {
								layer.confirm(
									lan.database.del_key_value_tips + ' [' + row.name + ']?',
									{
										title: lan.database.del_key_value,
										closeBtn: 2,
										icon: 0,
									},
									function (index) {
										bt_tools.send({ url: 'database/redis/del_redis_val', data: { data: JSON.stringify({ db_idx: id, key: row.name, sid: that.cloudInfo.sid }) } }, function (rdata) {
											if (rdata.status) {
												that.render_redis_table();
												that.change_tabs_num();
											}
											bt_tools.msg(rdata);
											layer.close(index);
										});
									}
								);
							},
						},
					],
				},
      ],
      tootls: [
				{
					type: 'search',
					positon: ['right', 'top'],
					placeholder: lan.database.search_key,
					searchParam: 'search', //搜索请求字段，默认为 search
					value: '', // 当前内容,默认为空
				},
				{
					type: 'batch',
					positon: ['left', 'bottom'],
					config: {
						title: ' delete',
						url: 'database/redis/del_redis_val',
						param: function (row) {
							return { data:JSON.stringify({db_idx:id,key:row.name,sid:that.cloudInfo.sid}) }
						},
						load: true,
						callback: function (that) {
							bt.confirm({ title: 'Batch delete Key', msg: 'Delete selected keys in batches. Do you want to continue?', icon: 0 }, function (index) {
								layer.close(index);
								that.start_batch({}, function (list) {
									var html = '';
									for (var i = 0; i < list.length; i++) {
										var item = list[i];
										html += '<tr>\
											<td>\
												<span class="text-overflow" title="' + item.name + '">' + item.name + '</span>\
											</td>\
											<td>\
												<div class="text-right"><span style="color:' + (item.request.status ? '#20a53a' : 'red') + '">' + item.request.msg + '</span></div>\
											</td>\
										</tr>';
									}
									database_table.$batch_success_table({ title: 'Batch delete Key', th: 'Key', html: html });
									database_table.$refresh_table_list(true);
								});
							});
						}
					}
				},
				{
					//分页显示
					type: 'page',
					positon: ['right', 'bottom'], // 默认在右下角
					pageParam: 'p', //分页请求字段,默认为 : p
					page: 1, //当前分页 默认：1
					numberParam: 'limit', //分页数量请求字段默认为 : limit
					number: 20, //分页数量默认 : 20条
					numberList: [10, 20, 50, 100, 200], // 分页显示数量列表
					numberStatus: true, //　是否支持分页数量选择,默认禁用
					jump: true, //是否支持跳转分页,默认禁用
				},
			],
      success: function () {
        var arry = [];
				var maxWidth = '';
				for (var i = 0; i < $('.size_ellipsis').length; i++) {
					arry.push($('.size_ellipsis').eq(i).width());
				}
				maxWidth = Math.max.apply(null, arry);
				$('.size_ellipsis').width(maxWidth + 5);
      }
    });
  },
	// 设置tabs的数量
	change_tabs_num: function () {
		var text = $('#redis_content_tab .tab-nav .on').text();
		var reg = new RegExp('(?<=\()(.+?)(?=\))');
		var num = text.match(reg)[0];
		if (!isNaN(num)) {
			num--;
			$('#redis_content_tab .tab-nav .on').text(text.replace(/\([0-9]\)/ig, '(' + num + ')'));
		}
	},
  // redis备份列表
  backup_redis_list: function () {
    var that = this;
		var redisBackupTable = null;
    bt_tools.open({
      title: 'Redis ' + lan.database.backup_list,
      area: '927px',
      btn: false,
      skin: 'redisBackupList',
      content: '<div id="redisBackupTable" class="pd20"></div>',
      success: function ($layer) {
        redisBackupTable = bt_tools.table({
          el: '#redisBackupTable',
          default: lan.database.backup_list_empty,
          height: 478,
          url: 'database/redis/get_backup_list',
          column:[
						{
							fid: 'name',
							title: lan.database.backup_name,
							width: 170,
							template: function (item) {
								return '<span class="flex" title="' + item.name + '"><span class="text-overflow">' + item.name + '</span></span>';
							},
						},
            {
							fid: 'filepath',
							title: lan.database.backup_path,
							template: function (item) {
								return '<span class="flex" title="' + item.filepath + '"><span class="text-overflow">' + item.filepath + '</span></span>';
							},
						},
            {
							fid: 'mtime',
							width: 140,
							title: lan.database.backup_time,
							type: 'text',
							template: function (row) {
								return '<span>' + bt.format_data(row.mtime) + '</span>';
							},
						},
						{
							fid: 'size',
							title: lan.database.backup_size,
							type: 'text',
							width: 120,
							template: function (row) {
								return '<span>' + bt.format_size(row.size) + '</span>';
							},
						},
            {
							fid: 'sid',
							width: 120,
							title: lan.database.backup_location,
							template: function (row) {
								var type_column = '-';
								var host = row.conn_config.db_host;
								var port = row.conn_config.db_port;
								switch (row.sid) {
									case '0':
										type_column = lan.database.add_auth_local;
										break;
									case '1':
										type_column = (lan.database.cloud_database + '(' + host + ':' + port + ')').toString();
										break;
									case '2':
										var list = database.cloudDatabaseList;
										$.each(list, function (index, item) {
											var db_host = item.db_host;
											var db_port = item.db_port;
											if (row.sid == item.id) {
												// 默认显示备注
												if (item.ps !== '') {
													type_column = item.ps
												} else {
													type_column = (lan.database.cloud_database + '(' + db_host + ':' + db_port + ')').toString();
												}
											}
										});
										break;
								}
								return '<span class="flex" title="' + type_column + '"><span class="text-overflow">' + type_column + '</span></span>';
							},
						},
						{
							type: 'group',
							title: lan.database.operation,
							align: 'right',
							width: 100,
							group: [
								{
									title: lan.database.backup_re,
									event: function (row) {
										bt.prompt_confirm(lan.database.backup_re_confirm_tit, lan.database.backup_re_confirm_cont1 + row.name + lan.database.backup_re_confirm_cont2, function () {
											bt_tools.send(
												{ url: 'database/redis/InputSql', data: { data: JSON.stringify({ file: row.filepath, sid: 0 }) } },
												function (rdata) {
													if (rdata.status) that.render_redis_content();
													bt_tools.msg(rdata);
												},
												lan.database.restore_data
											);
										});
									},
								},
								{
									title: lan.database.del,
									event: function (row) {
										layer.confirm(
											lan.database.del_backup_cont1 + row.name + lan.database.del_backup_cont2,
											{
												title: lan.database.del_backup,
												closeBtn: 2,
												icon: 0,
											},
											function (index) {
												bt_tools.send(
													{ url: 'database/redis/DelBackup', data: { data: JSON.stringify({ file: row.filepath }) } },
													function (rdata) {
														if (rdata.status) redisBackupTable.$refresh_table_list(true);
														bt_tools.msg(rdata);
														layer.close(index);
													},
													lan.database.del_backup_load
												);
											}
										);
									},
								},
							],
						},
          ],
          tootls: [
						{
							type: 'group',
							positon: ['left', 'top'],
							list: [
								{
									title: lan.database.backup_btn1,
									active: true,
									event: function () {
										bt_tools.send({ url: 'database/redis/ToBackup' }, function (rdata) {
											if (rdata.status) redisBackupTable.$refresh_table_list(true);
											bt_tools.msg(rdata);
										});
									},
								},
							],
						},
					],
					success: function () {
						if (!$layer) return;
						var height = $(window).height();
						var layerHeight = $layer.height();
						var top = (height - layerHeight) / 2;
						$layer.css('top', top);
					}
        })
      }
    })
  },
  // 添加/编辑redis库
  set_redis_library: function (row) {
    var that = this;
    var redis_form = null;
		bt_tools.open({
			title: (row ? lan.public.edit + ' [' + row.name + ']' : lan.public.add) + ' Key' + (!row ? ' to [' + that.cloudInfo.title + ']' : ''),
			area: '420px',
			btn: [row ? lan.public.save : lan.public.add, lan.public.cancel],
			content: '<div class="ptb20" id="redis_library_form"></div>',
			success: function (layers) {
				redis_form = bt_tools.form({
					el:'#redis_library_form',
					form: [
						{
							label: lan.public_backup.db,
							group: {
								type: 'select',
								name: 'db_idx',
								width: '260px',
								list: [
									{ title: 'DB0', value: 0 },
									{ title: 'DB1', value: 1 },
									{ title: 'DB2', value: 2 },
									{ title: 'DB3', value: 3 },
									{ title: 'DB4', value: 4 },
									{ title: 'DB5', value: 5 },
									{ title: 'DB6', value: 6 },
									{ title: 'DB7', value: 7 },
									{ title: 'DB8', value: 8 },
									{ title: 'DB9', value: 9 },
									{ title: 'DB10', value: 10 },
									{ title: 'DB11', value: 11 },
									{ title: 'DB12', value: 12 },
									{ title: 'DB13', value: 13 },
									{ title: 'DB14', value: 14 },
									{ title: 'DB15', value: 15 },
								],
								disabled: row ? true : false,
							},
						},
						{
							label: lan.public_backup.key,
							group: {
								type: 'text',
								name: 'name',
								width: '260px',
								placeholder: lan.database.key_input,
								disabled: row ? true : false,
							},
						},
						{
							label: lan.public_backup.value,
							group: {
								type: 'textarea',
								name: 'val',
								width: '260px',
								style: {
									'min-height': '100px',
									'line-height': '22px',
									'padding-top': '5px',
									resize: 'both',
								},
								placeholder: lan.database.value_input,
							},
						},
						{
							label: lan.database.term_of_validity,
							group: {
								type: 'number',
								name: 'endtime',
								width: '235px',
								placeholder: lan.database.term_of_validity_input,
								unit: lan.bt.s,
							},
						},
						{
							group: {
								type: 'help',
								style: { 'margin-left': '30px' },
								list: ['A validity period of 0 means permanent'],
							},
						},
					],
					data: row ? row : { db_idx: $('#redis_content_tab .tab-nav span.on').data('id') || undefined },
				});
				this.setLayerCenter(layers);
			},
			yes: function (indexs) {
				var formValue = redis_form.$get_form_value();
				if (formValue.name == '') return layer.msg(lan.database.key_input_tips);
				if (formValue.val == '') return layer.msg(lan.database.value_input_tips);
				if (formValue.endtime <= 0) delete formValue.endtime;
				if (row) {
					formValue['db_idx'] = $('#redis_content_tab .tab-nav span.on').data('id');
				}
				formValue['sid'] = that.cloudInfo.sid;
				bt_tools.send(
					{ url: 'database/redis/set_redis_val', data: { data: JSON.stringify(formValue) } },
					function (res) {
						if (res.status) {
							layer.close(indexs);
							that.render_redis_content(formValue.db_idx);
						}
						bt_tools.msg(res);
					},
					(row ? lan.database.redis_form_req1 : lan.database.redis_form_req2)
				);
			},
			setLayerCenter: function ($layer) {
				var height = $(window).height();
				var layerHeight = $layer.height();
				var top = (height - layerHeight) / 2;
				$layer.css('top', top);
			},
		});
  },
  // 选择需要清空的redis库
  choose_redis_list:function(){
    var that = this;
    layer.open({
      type: 1,
      area: '430px',
      title: lan.database.clear_redis_tit1 + '[' + this.cloudInfo.title + ']' + lan.database.clear_redis_tit2,
			btn: [lan.public.confirm, lan.public.cancel],
      shift: 5,
      closeBtn: 2,
      shadeClose: false,
      content:'\
			<div class="bt-form pd20" id="choose_redis_from">\
				<div class="line">\
					<span class="tname" style="width: 150px;">' + lan.database.select_database + '</span>\
					<div class="info-r">\
						<div class="rule_content_list">\
							<div class="rule_checkbox_group" bt-event-click="checkboxMysql" bt-event-type="active_all"><input name="*" type="checkbox" style="display: none;">\
								<div class="bt_checkbox_groups active"></div>\
								<span class="rule_checkbox_title">' + lan.database.all_select + '</span></div>\
							<ul class="rule_checkbox_list"></ul>\
						</div>\
					</div>\
				</div>\
			</div>',
      success: function(layers, index) {
        var rule_site_list = '';
        $.each(that.redisDBList,function(index,item){
          rule_site_list += '\
					<li>\
            <div class="rule_checkbox_group" bt-event-click="checkboxMysql" bt-event-type="active">\
            <span class="glyphicon glyphicon-menu-right" style="display:none" aria-hidden="true" bt-event-click="checkboxMysql" bt-event-type="fold"></span>\
          	<input name="'+ item.name +'" type="checkbox" data-id="'+item.id+'" checked=checked style="display: none;">\
            <div class="bt_checkbox_groups active"></div>\
            <span class="rule_checkbox_title">'+ item.name +'</span>\
            </div>\
          </li>';
          $('.rule_checkbox_list').html(rule_site_list);
          that.event_bind();
        });
      },
      yes: function (index, layers) {
				var redisIDList = [];
				$('#choose_redis_from .rule_checkbox_list input').each(function (index, el) {
					if ($(this).prop('checked')) {
						redisIDList.push($(this).data('id'));
					}
				});
				if (redisIDList.length == 0) return layer.msg(lan.database.clear_redis_tips1, { icon: 2 });
				layer.confirm(
					lan.database.clear_redis_confirm_cont,
					{
						title: lan.database.clear_redis_confirm_tit,
						closeBtn: 2,
						icon: 0,
					},
					function (index) {
						bt_tools.send({ url: 'database/redis/clear_flushdb', data: { data: JSON.stringify({ ids: JSON.stringify(redisIDList), sid: that.cloudInfo.sid }) } }, function (rdata) {
							if (rdata.status) {
								that.render_redis_content();
								layer.closeAll();
							}
							bt_tools.msg(rdata);
						});
					}
				);
			},
    })
  },
  event_bind:function(){
		$('.rule_checkbox_group')
		.unbind('click')
		.click(function (ev) {
			var _type = $(this).attr('bt-event-type'),
				_checkbox = '.bt_checkbox_groups';
			switch (_type) {
				case 'active_all': // 选中全部
					var thatActive = $(this).find(_checkbox),
						thatList = $(this).next();
					if (thatActive.hasClass('active')) {
						thatActive.removeClass('active').prev().prop('checked', false);
						thatList.find(_checkbox).removeClass('active').prev().prop('checked', false);
					} else {
						thatActive.addClass('active').prev().prop('checked', true);
						thatList.find(_checkbox).addClass('active').prev().prop('checked', true);
					}
					break;
				case 'active': // 激活选中和取消
					var thatActive = $(this).find(_checkbox),
						thatList = $(this).next();
					if (thatActive.hasClass('active')) {
						thatActive.removeClass('active').prev().prop('checked', false);
						$('.mysql_content_list>.mysql_checkbox_group input').prop('checked', false).next().removeClass('active');
						if (thatList.length == 1) {
							thatList.find(_checkbox).removeClass('active').prev().prop('checked', false);
						} else {
							var nodeLength = $(this).parent().siblings().length + 1,
								nodeList = $(this).parent().parent();
							if (nodeList.find('.bt_checkbox_groups.active').length != nodeLength) {
								nodeList.prev().find(_checkbox).removeClass('active').prev().prop('checked', false);
							}
						}
					} else {
						thatActive.addClass('active').prev().prop('checked', true);
						if (thatList.length == 1) {
							thatList.find(_checkbox).addClass('active').prev().prop('checked', true);
						} else {
							var nodeLength = $(this).parent().siblings().length + 1,
								nodeList = $(this).parent().parent();
							if (nodeList.find('.bt_checkbox_groups.active').length == nodeLength) {
								nodeList.prev().find(_checkbox).addClass('active').prev().prop('checked', true);
							}
						}
					}
					break;
				case 'fold': //折叠数据库列表
					if ($(this).hasClass('glyphicon-menu-down')) {
						$(this).removeClass('glyphicon-menu-down').addClass('glyphicon-menu-right').parent().next().hide();
					} else {
						$(this).removeClass('glyphicon-menu-rigth').addClass('glyphicon-menu-down').parent().next().show();
					}
					break;
			}
			$('.rule_content_list').removeAttr('style');
			ev.stopPropagation();
		});	
  },
  // 重置时间格式
  reset_time_format: function (time) {
		if (time == 0) return lan.public_backup.permanent;
		var theTime = parseInt(time); // 秒
		var middle = 0; // 分
		var hour = 0; // 小时

		if (theTime > 60) {
			middle = parseInt(theTime / 60);
			theTime = parseInt(theTime % 60);
			if (middle > 60) {
				hour = parseInt(middle / 60);
				middle = parseInt(middle % 60);
			}
		}
		var result = '' + parseInt(theTime) + ' ' + lan.site.second + (theTime > 1 ? 's' : '');
		if (middle > 0) {
			result = '' + parseInt(middle) + ' ' + lan.crontab.minute + (middle > 1 ? 's' : '') + ' ' + result;
		}
		if (hour > 0) {
			result = '' + parseInt(hour)  + ' ' + lan.crontab.hour  + (hour > 1 ? 's' : '') + ' ' + result;
		}
		return result;
	},
}

var pgsql ={
	// 数据库表格实例
	databaseTable: null,
	// 获取数据库列表
  getDatabaseList: function (config) {
		if (this.databaseTable) {
			config = config || {};
			if (config.isInit) this.databaseTable.config.page.page = 1;
			this.databaseTable.$refresh_table_list(true);
			return;
		}

		var _that = this;
		var type = database.getType();
    var param = { table: 'databases', search: '' };

    $('#bt_pgsql_table').empty();
    this.databaseTable = bt_tools.table({
      el: '#bt_pgsql_table',
      url: 'database/' + type + '/get_list',
      param: param, // 参数
      minWidth: '1000px',
      load: true,
      autoHeight: true,
      default: 'The database list is empty', // 数据为空时的默认提示
      pageName: 'database',
      beforeRequest:function(beforeData){
        var db_type_val = $('input[name="db_type_filter_' + type + '"]').val();
        switch(db_type_val){
          case 'all':
            delete param['db_type']
            delete param['sid']
            break;
          case 0:
            param['db_type'] = 0;
            break;
          default:
            delete param['db_type'];
            param['sid'] = db_type_val
        }
        if (beforeData.hasOwnProperty('data') && typeof beforeData.data === 'string') {
          delete beforeData['data']
          return { data: JSON.stringify($.extend(param,beforeData)) }
        }
        return {data:JSON.stringify(param)}
      },
			sortParam: function (data) {
        return { 'order': data.name + ' ' + data.sort };
      },
      column:[
        { type: 'checkbox', width: 20 },
        { fid: 'name', title: lan.database.add_name },
        { fid: 'username', title: lan.database.user, sort: true },
        {
					fid: 'password',
					title: lan.database.add_pass,
					type: 'password',
					copy: true,
					eye_open: true
				},
        {
          fid:'backup',
          title: lan.database.backup,
          width: 130,
          template: function (item) {
            var backup = lan.database.backup_empty;
            var _class = "bt_warning";
            if (item.backup_count > 0) {
							backup = lan.database.backup_ok;
							_class = 'bt_success';
						}
						var num = item.backup_count > 0 ? '(' + item.backup_count + ')' : '';
						// 备份链接
						var backupLink = '<a href="javascript:;" class="btlink ' + _class + '" onclick="database.showBackupList(' + item.id + ", '" + item.name + '\')">' + backup + num + '</a>';
						// 导入链接
						var importLink = '<a href="javascript:;" class="btlink" onclick="database.showImport(\'' + item.name + '\')">' + lan.database.input + '</a>';
						return '<span>' + backupLink + ' | ' + importLink + '</span>';
          }
        },
        {
          fid: 'position',
          title: lan.database.position,
          type: 'text',
          width: 116,
          template: function (row) {
            var type_column = '-';
						var host = row.conn_config.db_host;
						var port = row.conn_config.db_port;
            switch(row.db_type){
              case 0:
                type_column = lan.database.add_auth_local;
                break;
              case 1:
                type_column = (lan.database.cloud_database + '(' + host + ':' + port + ')').toString();
                break;
              case 2:
								var list = database.cloudDatabaseList;
                $.each(list, function(index, item) {
									var db_host = item.db_host;
									var db_port = item.db_port;
                  if (row.sid == item.id) {
										// 默认显示备注
                    if (item.ps !== '') {
                      type_column = item.ps
                    } else {
                      type_column = (lan.database.cloud_database + '(' + db_host + ':' + db_port + ')').toString();
                    }
                  }
                })
                break;
            }
            return '<span class="flex" title="' + type_column + '"><span class="text-overflow">' + type_column + '</span></span>';
          }
        },
        {
          fid: 'ps',
          title: lan.database.add_ps,
          type: 'input',
          blur: function (row, index, ev) {
            bt.pub.set_data_ps({
              id: row.id,
              table: 'databases',
              ps: ev.target.value
            }, function (res) {
              layer.msg(res.msg, (res.status ? {} : {
                icon: 2
              }));
            });
          },
          keyup: function (row, index, ev) {
            if (ev.keyCode === 13) {
              $(this).blur();
            }
          }
        },
        {
          type: 'group',
          title: lan.database.operation,
          width: 150,
          align: 'right',
          group: [{
            title: lan.database.edit_pass,
            tips: lan.database.edit_pass_title,
            hide: function (rows) { return rows.db_type == 1 },
            event: function (row) {
              database.set_data_pass(row.id, row.username, row.password);
            }
          }, {
            title: lan.database.del,
            tips: lan.database.del_title,
            event: function (row) {
              database.del_database(row.id, row.name, row);
            }
          }]
        }
      ],
			// 按钮组
      tootls: [
				{
					type: 'group',
					positon: ['left', 'top'],
					list: [
						{
							title: lan.database.add_title,
							active: true,
							event: function () {
								database.getCloudServerList(function (list) {
									bt.database.add_database(list,function (res) {
										if (res.status) _that.getDatabaseList();
									});
								});
							}
						},
						{
							title: lan.database.edit_root,
							event: function () {
								bt.database.set_root('pgsql')
							}
						},
						{
							title: lan.database.cloud_server,
							event: function () {
								database.open_cloud_server();
							}
						},
						{
							title: 'Sync all',
							style:{'margin-left':'30px'},
							event: function () {
								bt.database.sync_to_database({type:0,data:[]},function(res){
									if(res.status) _that.getDatabaseList();
								})
							}
						},
						{
							title: 'Get DB from server',
							event: function () {
								database.getCloudServerList(function (list) {
									bt_tools.open({
										title: lan.database.select_position,
										area: '450px',
										btn: [lan.public.confirm, lan.public.cancel],
										skin: 'databaseCloudServer',
										content: {
											'class':'pd20',
											form:[{
												label: lan.database.position,
												group:{
													type: 'select',
													name: 'sid',
													width: '260px',
													list: list
												}
											}]
										},
										success: function (layers) {
											$(layers).find('.layui-layer-content').css('overflow','inherit');
										},
										yes:function (form, layers, index){
											bt.database.sync_database(form.sid, function (rdata) {
												if (rdata.status){
													_that.getDatabaseList();
													layer.close(layers)
												}
											});
										}
									});
								});
							}
        		}
					]
      	},
				{
					type: 'batch', // batch_btn
					positon: ['left', 'bottom'],
					placeholder: 'Select batch operation',
					buttonValue: 'Execute',
					disabledSelectValue: 'Select the DB to execute!!',
					selectList: [
						{
							title: 'Sync to Server',
							url: '/database/' + type + '/SyncToDatabases',
							paramName: 'data', // 列表参数名,可以为空
							th: 'Database Name',
							beforeRequest: function(list) {
								var arry = [];
								$.each(list, function (index, item) {
									arry.push(item.id);
								});
								return JSON.stringify({ids:JSON.stringify(arry),type:1})
							},
							success: function (res, list, that) {
								layer.closeAll();
								var html = '';
								$.each(list, function (index, item) {
									html += '\
									<tr>\
										<td>' + item.name + '</td>\
										<td class="text-right"><span style="color:' + (res.status ? '#20a53a' : 'red') + '">' + res.msg + '</span></td>\
									</tr>';
								});
								that.$batch_success_table({
									title: 'Batch sync selected',
									th: 'Database Name',
									area: '450px',
									html: html
								});
							}
						},
						{
							title: 'Database Backup',
							url: type == 'mysql' ? 'database?action=ToBackup' : '/database/' + type + '/ToBackup',
							load: true,
							param: function (row) {
								return type == 'mysql' ? { id: row.id } : {data:JSON.stringify({id: row.id})}
							},
							// 手动执行,data参数包含所有选中的站点
							callback: function (that) {
								that.start_batch({}, function (list) {
									var html = '';
									for(var i=0;i<list.length;i++){
										var item = list[i];
										html += '<tr><td>'+ item.name +'</td><td><div style="float:right;"><span style="color:'+ (item.request.status?'#20a53a':'red') +'">'+ item.request.msg +'</span></div></td></tr>';
									}
									_that.databaseTable.$batch_success_table({
										title: 'Batch backup database',
										th: 'Database Name',
										html: html,
										area: '480px',
									});
									_that.getDatabaseList();
								});
							}
						},
						{
							title: 'Delete database',
							url: '/database/' + type + '/DeleteDatabase',
							load: true,
							param: function (row) {
								return {
									data: JSON.stringify({ id: row.id, name: row.name })
								}
							},
							callback: function (that) { // 手动执行,data参数包含所有选中的站点
								var ids = [];
								for (var i = 0; i < that.check_list.length; i++) {
									ids.push(that.check_list[i].id);
								}
								database.del_database(ids,function(param){
									that.start_batch(param, function (list) {
										layer.closeAll()
										var html = '';
										for (var i = 0; i < list.length; i++) {
											var item = list[i];
											html += '\
											<tr>\
												<td>' + item.name + '</td>\
												<td class="text-right">\
													<span style="color:' + (item.request.status ? '#20a53a' : 'red') + '">' + item.request.msg + '</span>\
												</td>\
											</tr>';
										}
										database_table.$batch_success_table({
											title: 'Batch deletion',
												th: 'Database Name',
											html: html
										});
										_that.getDatabaseList();
									});
								})
							}
						}
					]
				},
				{
					type: 'search',
					positon: ['right', 'top'],
					placeholder: lan.database.database_search,
					searchParam: 'search', //搜索请求字段，默认为 search
					value: '',// 当前内容,默认为空
				},
				{ 
					type: 'page', // 分页显示
					positon: ['right', 'bottom'], // 默认在右下角
					pageParam: 'p', // 分页请求字段,默认为 : p
					page: 1, // 当前分页 默认：1
					numberParam: 'limit', // 分页数量请求字段默认为 : limit
					number: 20, // 分页数量默认 : 20条
					numberList: [10, 20, 50, 100, 200], // 分页显示数量列表
					numberStatus: true, //是否支持分页数量选择,默认禁用
					jump: true, // 是否支持跳转分页,默认禁用
				}
			]
    });
		database.renderCloudServerSelect();
  }
}

database.init();
