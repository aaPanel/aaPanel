var firewall = {
	init: function () {
		this.event();

		var name = bt.get_cookie('firewall_type');
		$('[data-name="'+ (name || 'safety') +'"]').trigger('click');
	},
	event: function () {
		// 切换主菜单
		$('#cutTab .tabs-item').click(function () {
			var index = $(this).index();
			var name = $(this).data('name');
			var $cont = $('.firewall-tab-view').children('.tab-con').eq(index);
			bt.set_cookie('firewall_type',name)

			$(this).addClass('active').siblings().removeClass('active');
			$('.state-content').hide().children().hide();
			$cont.addClass('show w-full').removeClass('hide').siblings().removeClass('show w-full').addClass('hide');

			switch (name) {
        case 'safety':
          safety.init();
          break;
				case 'ssh':
          ssh.init();
          break;
				case 'intrusion':
					intrusion.init();
					break;
				case 'system':
					system.init();
					break;
				case 'logAudit':
					logAudit.init();
					break;
				case 'logs':
					logs.init();
					break;
      }
		});

		// 切换子菜单
		$('.tab-nav-border').on('click', 'span', function () {
			var index = $(this).index();
			var $cont = $(this).parent().nextAll('.tab-nav-con').children('.tab-block').eq(index);

			$(this).addClass('on').siblings('.on').removeClass('on');
			$cont.addClass('on').siblings('.on').removeClass('on');
		});

		safety.event();
		ssh.event();
		intrusion.event();
		system.event();
		logAudit.event();
		logs.event();
	},

	/**
   * @description 渲染日志分页
   * @param pages
   * @param p
   * @param num
   * @returns {string}
   */
  renderLogsPages:function(pages,p,num){
    return (num >= pages?'<a class="nextPage" data-page="1">首页</a>':'') + (p !== 1?'<a class="nextPage" data-page="'+ (p-1) +'">上一页</a>':'') + (pages <= num?'<a class="nextPage" data-page="'+ (p+1) +'">下一页</a>':'')+'<span class="Pcount">Page '+ p +' </span>';
  }
}

// 系统防火墙
var safety = {
	init: function () {
		$('.state-content').show();
		$('.state-content .safety-header').show();

		this.getFirewallInfo();
		
		bt.firewall.get_logs_size(function(rdata){
			$("#logSize").text(rdata);
		});

		$('#safety .tab-nav-border span').eq(0).trigger('click');
	},
	event: function () {
		var that = this;

		// 切换系统防火墙菜单事件
		$('#safety').unbind('click').on('click', '.tab-nav-border span', function () {
			var index = $(this).index();
			that.cutFirewallTab(index);
		});

		// 防火墙开关
		$('#isFirewall').unbind('click').click(function(){
			var _that = $(this)
			var status = !_that.prop("checked")
			bt.confirm({
				title: (status ? lan.security.firewall.switchTit3 : lan.security.firewall.switchTit2) + lan.security.firewall.switchTit1,
				msg: (status ? lan.security.firewall.switchMsg1 : lan.security.firewall.switchMsg2),
				cancel: function () {
					_that.prop("checked", status);
				}
			},function () {
				bt_tools.send({
					url:'/safe/firewall/firewall_admin',
					data:{data: JSON.stringify({status:!status?'start':'stop'})},
				},function(rdata){
					bt_tools.msg(rdata);
					setTimeout(function(){
						location.reload();
					},2000)
				}, lan.security.firewall.switchMsg3)
			},function () {
				_that.prop("checked",status)
			})
		});
		// 禁用ping
		$('#ssh_ping').unbind('click').on('click',function (){
			var _that = $(this), status = _that.prop("checked")?0:1;
			bt.firewall.ping(status,function(rdata){
				if(rdata === -1){
					_that.prop('checked',!!status);
				}else{
					bt.msg(rdata);
				}
			});
		});
		// 清空日志
		$('#clearWebLogs').click(function () {
			that.clear_logs_files();
		});
	},
	/**
	 * @description 切换系统防火墙菜单
	 * @param {number} index 索引
	 */
	cutFirewallTab: function (index) {
		switch (index) {
			case 0:
				this.portRuleTable()
				break;
			case 1:
				this.ipRuleTable()
				break;
			case 2:
				this.portForwardTable()
				break;
			case 3:
				this.countryRegionTable()
				break;
		}
	},
	getFirewallInfo: function (load) {
		bt_tools.send({
			url: '/safe/firewall/get_firewall_info',
		}, function (rdata) {
			$('#isFirewall').prop("checked", rdata.status);
			$('#ssh_ping').prop('checked', !rdata.ping);
			$('#safety .tab-nav-border span:eq(0) > i').html(rdata.port);
			$('#safety .tab-nav-border span:eq(1) > i').html(rdata.ip);
			$('#safety .tab-nav-border span:eq(2) > i').html(rdata.trans);
			$('#safety .tab-nav-border span:eq(3) > i').html(rdata.country);
		}, load ? lan.security.firewall.get_firewall_info : '');
	},
	/**
	 * @description 清空日志
	 */
	clear_logs_files:function(){
		bt.show_confirm(lan.security.firewall.clearTit1, lan.security.firewall.clearMsg1, function () {
			bt.firewall.clear_logs_files(function(rdata){
				$("#logSize").text(rdata);
				bt.msg({msg:lan.firewall.empty,icon:1});
			});
		});
	},
	/**
	 * @description 渲染系统防火墙端口规则
	 */
	portRuleTable: function () {
		var that = this;
		var portsPs = {
			"80": lan.firewall.site_default_port,
			"3306": lan.firewall.mysql_default_port,
			"888": lan.firewall.phpmmyadmin_default_port,
			"22": lan.firewall.ssh_default_port,
			"20": lan.firewall.ftp1_default_port,
			"21": lan.firewall.ftp_default_port,
			"39000-40000": lan.firewall.ftp2_default_port,
			"30000-40000": lan.firewall.ftp2_default_port,
			"11211": lan.firewall.mem_default_port,
			"873": lan.firewall.rsync_default_port,
			"8888": lan.firewall.bt_default_port
		}
		var fireWallTable = bt_tools.table({
			el: '#portRules',
			url: '/safe/firewall/get_rules_list',
			load: lan.security.firewall.port.load,
			default: lan.security.firewall.port.default, // 数据为空时的默认提示
			autoHeight: true,
			beforeRequest: 'model',
			tootls: [
				{ // 按钮组
					type: 'group',
					list: [{
						title: lan.security.firewall.add_btn,
						active: true,
						event: function (ev) {
							that.editPortRule()
						}
					}, {
						title: lan.security.firewall.import_btn,
						event: function (ev) {
							that.ruleImport('port_rule')
						}
					}, {
						title: lan.security.firewall.export_btn,
						event: function (ev) {
							that.ruleExport('port_rule')
						}
					}]
				},
				{ // 搜索内容
					type: 'search',
					placeholder: lan.security.firewall.port.search,
					searchParam: 'query', //搜索请求字段，默认为 search
				},
				{ //分页显示
					type: 'page',
					numberStatus: true, //　是否支持分页数量选择,默认禁用
					jump: true, //是否支持跳转分页,默认禁用
				},
				{
					type: 'batch', // 批量操作
					disabledSelectValue: lan.firewall.batch_disabled_tips('port'),
					placeholder: 'Select batch operation',
          buttonValue: 'Execute',
					selectList: [
						{
							load: true,
							title: lan.firewall.batch_del_btn('port'),
							url: '/safe/firewall/remove_rules',
							param: function (row) {
								return { data: JSON.stringify(row) };
							},
							refresh: true,
							callback: function (that) {
								bt.confirm({ title: lan.firewall.batch_del_title('port'), msg: lan.firewall.batch_del_msg('port') }, function () {
									var param = {};
									that.start_batch(param, function (list) {
										var html = '';
										for (var i = 0; i < list.length; i++) {
											var item = list[i];
											html +=
												'<tr><td>Port: ' +
												item.ports +
												'</td><td><div style="float:right;"><span style="color:' +
												(item.request.msg.indexOf('Success') > -1 ? '#20a53a' : 'red') +
												'">' +
												item.request.msg +
												'</span></div></td></tr>';
										}
										fireWallTable.$batch_success_table({ title: lan.firewall.batch_del_title('port'), th: 'Port', html: html });
										fireWallTable.$refresh_table_list(true);
										safety.getFirewallInfo();
									});
								});
							},
						},
					],
				}
			],
			column: [
				{type: 'checkbox', class: '', width: 20},
				{ title: lan.security.firewall.protocol, fid: 'protocol', width: 100 },
				{ title: lan.security.firewall.ports, fid: 'ports', width: 200 },
				{
					field: 'status',
					title: lan.security.firewall.status + '<a href="https://www.aapanel.com/forum/d/1088-description-of-firewall-status" class="bt-ico-ask" target="_blank" title="' + lan.security.firewall.port.th3_click + '">?</a>',
					width: 150,
					type: 'text',
					template: function (item) {
						var status = '';
						switch (item.status) {
							case 0:
								status = lan.firewall.status_not;
								break;
							case 1:
								status = lan.firewall.status_net;
								break;
							default:
								status = lan.firewall.status_ok;
								break;
						}
						return '<span>' + status + ((item.status !=0 && item.status !==1)? ' (<a class="btlink">Details</a>)</span>':'</span>');
					},
					event: function (item) {
						var param = {
							port: item.ports,
						};
						if (item.status == 0) {
							return false;
						}
						bt_tools.send({
							url: '/safe/firewall/get_listening_processes',
							data: { data: JSON.stringify(param) },
						}, function (rdata) {
							layer.open({
								content:
									'\
											<div class="divtable daily-table" style="padding: 20px; min-height: 160px;">\
													<table class="table table-hover">\
															<tbody>\
															</tbody>\
													</table>\
											</div>\
									',
								title: '[' + item.ports + '] ' + lan.firewall.port_use_title,
								closeBtn: 2,
								type: 1,
								area: ['450px', 'auto'],
								shadeClose: true,
								success: function (layero, index) {
									layero.find('.layui-layer-content').css('height', 'auto')

									var html = '';
									function getName(name) {
										if (name == 'process_name') {
											return  lan.firewall.process_name + ':';
										} else if (name == 'process_pid') {
											return lan.firewall.process_pid + ':';
										} else if (name == 'process_cmd') {
											return lan.firewall.start_command + ':';
										}
									}
									var keys = Object.keys(rdata);
									for (var i = 0; i < keys.length; i++) {
										html +=
											'\
										<tr class="daily-title" style="font-weight: bold;background: #f7f7f7">\
											<td width="120" style="border-right: 1px solid #ddd;">' +
											getName(keys[i]) +
											'</td>\
											<td  style="background-color: #ffff;overflow: auto;border-right: 1px solid #ddd;">' +
											rdata[keys[i]] +
											'</td>\
										</tr>';
									}
									$('.daily-table tbody').html(html);
								},
							});
						}, lan.firewall.port_use_load);
					},
				},
				{
					title: lan.security.firewall.strategy,
					fid: 'types',
					width: 80,
					event: function (row) {
						var status = !(row.types === 'accept');
						bt.confirm(
							{
								title: lan.security.firewall.port.modify_strategy_tit + ' [' + row.ports + ']',
								msg: status ? 
									lan.security.firewall.port.modify_strategy_msg1 : 
									lan.security.firewall.port.modify_strategy_msg2,
							},
							function () {
								var param = $.extend(row, { types: row.types === 'accept' ? 'drop' : 'accept', source: row.address });
								delete param.addtime;
								delete param.address;
								bt_tools.send(
									{
										url: '/safe/firewall/modify_rules',
										data: { data: JSON.stringify(param) },
									},
									function (rdata) {
										bt_tools.msg(rdata);
										that.portRuleTable();
									},
									lan.security.firewall.port.modify_strategy_req
								);
							}
						);
					},
					template: function (row) {
						return row.types === 'accept'
							? '<a href="javascript:;" class="bt_success">' + lan.security.firewall.allow + '</a>'
							: '<a href="javascript:;" class="bt_danger">' + lan.security.firewall.deny + '</a>';
					},
				},
				{
					title: lan.security.firewall.source_ip,
					fid: 'address',
					width: 100,
					template: function (row) {
						return row.address === '' ? '<span>' + lan.security.firewall.all + '</span>' : '<span title="' + row.address + '">' + row.address + '</span>';
					},
				},
				{
					title: lan.security.firewall.remarks,
					fid: 'brief',
					type: 'text',
					template: function (row) {
						if (row.brief) return '<span>' + row.brief + '</span>';
						if (row.ports in portsPs) return '<span>' + portsPs[row.ports] + '</span>';
						return '<span>' + row.brief + '</span>';
					}
				},
				{ title: lan.security.firewall.add_time, fid: 'addtime', width: 150 },
				{
					title: lan.public.operate,
					type: 'group',
					width: 150,
					align: 'right',
					group: [
						{
							title: lan.public.edit,
							event: function (row, index) {
								that.editPortRule(row);
							}
						},
						{
							title: lan.public.del,
							event: function (row, index) {
								that.removePortRule(row);
							}
						}
					]
				}
			]
		})
	},
	/**
     * @description 添加/编辑端口规则
     * @param {object} row 数据
     */
	editPortRule: function (row) {
		var isEdit = !!row, that = this;
		row = row || { protocol:'tcp',ports:'',types:'accept',address:'',brief:''}
		layer.open({
			type: 1,
			area:"420px",
			title: (!isEdit ? lan.public.add : lan.public.edit) + lan.security.firewall.port.form_title,
			closeBtn: 2,
			shift: 5,
			shadeClose: false,
			btn: ['Confirm', 'Cancel'],
			content: '<form id="editPortRuleForm" class="bt-form bt-form pd20" onsubmit="return false"></form>',
			yes:function(index,layers){
				bt_tools.verifyForm('#editPortRuleForm',[
					{
						name: 'ports',
						validator: function (value) {
							if (!value) return lan.security.firewall.port.form_port_empty;
						},
					},
					{
						name: 'address',
						validator: function (value, row) {
							if (!value && row.choose !== 'all') return lan.security.firewall.port.form_address_empty;
						},
					},
				], function(verify,form){
					if(verify){
						if(isEdit) form.address = form.choose === 'all'?'':form.address;
						form['source'] = form.address;
						// 添加、修改
						bt_tools.send({
							url: '/safe/firewall/' + (isEdit ? 'modify_rules' : 'create_rules'),
							data: {data: JSON.stringify($.extend({id: row.id}, form))}
						}, function (rdata) {
							bt.msg(rdata);
							if (rdata.status) {
								layer.close(index);
								that.portRuleTable();
								that.getFirewallInfo();
							}
						}, (isEdit ? lan.public.edit : lan.public.add) + lan.security.firewall.port.form_title);
					}
				})
			},
			success:function(layero, index){
				bt_tools.fromGroup('#editPortRuleForm', [
					{
						label: lan.security.firewall.protocol,
						width: '200px',
						name: 'protocol',
						type: 'select',
						options: [
							{ value: 'tcp', label: 'TCP' },
							{ value: 'udp', label: 'UDP' },
							{ value: 'tcp/udp', label: 'TCP/UDP' },
						],
					},
					{
						label: lan.security.firewall.ports,
						width: '200px',
						name: 'ports',
						readonly: isEdit,
						type: 'text',
						placeholder: lan.security.firewall.port.form_port,
					},
					{
						label: lan.security.firewall.source_ip,
						width: '200px',
						name: 'choose',
						type: 'select',
						options: [
							{ value: 'all', label: lan.security.firewall.all },
							{ value: 'point', label: lan.security.firewall.specify_ip },
						],
						on: {
							change: function (ev, val, el) {
								$(this).data('line').next().toggle();
							},
						},
					},
					{
						label: '',
						width: '200px',
						name: 'address',
						placeholder: lan.security.firewall.port.form_specify_ip,
						labelStyle: row.address !== '' ? '' : 'display: none'
					},
					{
						label: lan.security.firewall.strategy,
						width: '200px',
						name: 'types',
						type: 'select',
						options: [
							{ value: 'accept', label: lan.security.firewall.allow },
							{ value: 'drop', label: lan.security.firewall.deny },
						],
					},
					{ label: lan.security.firewall.remarks, width: '200px', name: 'brief', type: 'text' },
					{
						type: 'tips',
						style: 'padding-left: 30px; margin-top:5px;',
						list: [
							lan.security.firewall.port.form_tips1, 
							lan.security.firewall.port.form_tips2
						],
					}
				], $.extend(row,{ choose: row.address ? 'point' : 'all' }))
				if (isEdit) $('[name="ports"]').css({ 'background-color': '#eee', 'cursor': 'no-drop' });
				bt_tools.setLayerArea(layero);
			}
		});
	},
	/**
     * @description 规则导入
     * @param
     */
	ruleImport: function (name){
		var _this = this;
		layer.open({
			type: 1,
			area: '360px',
			title: lan.security.firewall.import_tit,
			closeBtn: 2,
			shift: 5,
			shadeClose: false,
			btn: [lan.public.import, lan.public.cancel],
			content:'\
			<div class="bt-form-new port-import-form">\
				<div class="form-item">\
					<div class="form-value c4">\
						<div class="detect_input">\
							<input type="text" class="input_file" placeholder="' + lan.security.firewall.import_file + '">\
							<input type="file" class="file_input hide" id="fileInput" />\
							<button type="button" class="select_file" onclick="$(\'#fileInput\').click()">' + lan.security.firewall.import_btn + '</button>\
						</div>\
					</div>\
				</div>\
			</div>',
			yes: function (index, layers) {
				if (!$("#fileInput")[0].files[0]) {
					layer.msg(lan.security.firewall.import_file_tips, { icon: 2 });
					return false;
				}
				_this.upload({name:name, _fd:$("#fileInput")[0].files[0]}, 0, index);
			},
			success: function () {
				$("#fileInput").on('change', function () {
					if (!$("#fileInput")[0].files[0]) {
						$(".input_file").val("");
					}
					var filename = $("#fileInput")[0].files[0].name;
					$(".input_file").val(filename);
				});
			},
		});
	},

	/**
	 * @description 规则导出
	 */
	ruleExport: function (type){
		bt_tools.send({
			url: '/safe/firewall/export_rules',
			data: { data: JSON.stringify({ rule_name: type }) },
		}, function (rdata) {
			if (rdata.status) {
				window.open('/download?filename=' + rdata.msg);
			} else {
				bt_tools.msg(rdata);
			}
		}, lan.security.firewall.export_req);
	},

	/**
	 * @description 删除端口规则
	 * @param {object} row 行数据
	 */
	removePortRule: function (row){
		var that = this;
		bt.confirm({
			title: lan.security.firewall.port.del_tit + '[' + row.ports + ']',
			msg: lan.security.firewall.port.del_msg
		}, function () {
			bt_tools.send({
				url: '/safe/firewall/remove_rules',
				data: { data: JSON.stringify(row) }
			}, function (rdata) {
				bt.msg(rdata);
				if (rdata.status) {
					that.portRuleTable();
					that.getFirewallInfo();
				}
			}, lan.security.firewall.port.del_req);
		});
	},
	/**
	 * @description 规则导入请求
	 * @param s_data
	 * @param start
	 * @param index
	 */
	upload: function (s_data, start, index) {
		var _this = this;
		var fd = s_data._fd;
		var end = Math.min(fd.size, start + 1024*1024*2);
		var form = new FormData();
		form.append("f_path", "/www/server/panel/data/firewall");
		form.append("f_name", fd.name);
		form.append("f_size", fd.size);
		form.append("f_start", start);
		form.append("blob", fd.slice(start, end));
		$.ajax({
			url: '/files?action=upload',
			type: "POST",
			data: form,
			async: true,
			processData: false,
			contentType: false,
			success: function (data) {
				if (typeof (data) === "number") {
					_this.upload(s_data, data, index)
				} else {
					if (data.status) {
						bt_tools.send({
							url:'/safe/firewall/import_rules',
							data:{data:JSON.stringify({rule_name:s_data.name, file_name:fd.name})}
						},function(res){
							bt_tools.msg(res);
							if(res.status){
								layer.close(index);
								if(s_data.name === 'port_rule'){ _this.portRuleTable() }
								else if(s_data.name === 'ip_rule'){ _this.ipRuleTable() }
								else if(s_data.name === 'country_rule'){ _this.countryRegionTable() }
								else{ _this.portForwardTable() }
							}
						}, lan.security.firewall.import_req)
					}
				}
			},
			error: function (e) {
				console.log("上传规则文件出问题喽!")
			}
		})
	},
	/**
	 * @description ip规则列表
	 */
	ipRuleTable: function () {
		var that = this;
		var ruleTable = bt_tools.table({
			el: '#ipRule',
			url: '/safe/firewall/get_ip_rules_list',
			load: lan.security.firewall.ip.load,
			default: lan.security.firewall.ip.default, // 数据为空时的默认提示
			autoHeight: true,
			beforeRequest: 'model',
			tootls: [
				{ // 按钮组
					type: 'group',
					list: [
						{
						title: lan.security.firewall.add_btn,
						active: true,
						event: function (ev) {
							that.editIpRule()
						}
						},
						{
							title: lan.security.firewall.import_btn,
							event: function (ev) {
								that.ruleImport('ip_rule')
							}
						},
						{
							title: lan.security.firewall.export_btn,
							event: function (ev) {
								that.ruleExport('ip_rule')
							}
						}
					]
				},
				{ // 搜索内容
					type: 'search',
					placeholder: lan.security.firewall.ip.search,
					searchParam: 'query', //搜索请求字段，默认为 search
				},
				{
					type: 'batch', // 批量操作
					disabledSelectValue: lan.firewall.batch_disabled_tips('IP'),
					placeholder: 'Select batch operation',
          buttonValue: 'Execute',
					selectList: [
						{
							title: lan.firewall.batch_del_btn('IP'),
							url: '/safe/firewall/remove_ip_rules',
							load: true,
							param: function (row) {
								return {
									data: JSON.stringify(row),
								};
							},
							refresh: true,
							callback: function (that) {
								bt.confirm({ title: lan.firewall.batch_del_title('IP'), msg: lan.firewall.batch_del_msg_ip }, function () {
									var param = {};
									that.start_batch(param, function (list) {
										var html = '';
										for (var i = 0; i < list.length; i++) {
											var item = list[i];
											html +=
												'<tr><td>' +
												item.address +
												'</td><td><div style="float:right;"><span style="color:' +
												(item.request.msg.indexOf('Success') > -1 ? '#20a53a' : 'red') +
												'">' +
												item.request.msg +
												'</span></div></td></tr>';
										}
										ruleTable.$batch_success_table({ title: lan.firewall.batch_del_title('IP'), th: lan.firewall.batch_del_ip_name, html: html });
										ruleTable.$refresh_table_list(true);
										safety.getFirewallInfo();
									});
								});
							},
						},
					],
				},
				{ //分页显示
					type: 'page',
					numberStatus: true, //　是否支持分页数量选择,默认禁用
					jump: true, //是否支持跳转分页,默认禁用
				}
			],
			column: [
				{type: 'checkbox', class: '', width: 20},
				{fid: 'address', title: lan.security.firewall.source_ip, width: 150},
				{fid: 'area', title: lan.security.firewall.ip_home + '&nbsp;' + (parseInt(bt.get_cookie('pro_end')) < 0?'<a href="javascript:;" class="btlink" onclick="bt.soft.updata_pro(116)">Pro</a>':''), template: function(row){
					var area = row.area;
					return '<span>'+ (area.continent || '') + (area.info || '--') +'</span>'
				}},
				{
					fid: 'types',
					title: lan.security.firewall.strategy,
					width: 100,
					event:function (row){
						var status = !(row.types === 'accept')
						bt.confirm({
							title: lan.security.firewall.ip.modify_strategy_tit + ' [' + row.address + ']',
							msg: (status ? lan.security.firewall.ip.modify_strategy_msg1 : lan.security.firewall.ip.modify_strategy_msg2),
						},function () {
							var param = $.extend(row, { types:row.types === 'accept' ? 'drop' : 'accept' });
							bt_tools.send({
								url: '/safe/firewall/modify_ip_rules',
								data: { data: JSON.stringify(param) }
							}, function (rdata) {
								bt_tools.msg(rdata);
								that.ipRuleTable();
							}, lan.security.firewall.ip.modify_strategy_req);
						});
					},
					template: function (row) {
						return row.types === 'accept' ? 
							'<span class="bt_success cursor-pointer">' + lan.security.firewall.release + '</span>' :
							'<span class="bt_danger cursor-pointer">' + lan.security.firewall.block + '</span>';
					}
				},
				{fid: 'brief', title: lan.security.firewall.remarks },
				{fid: 'addtime', title: lan.security.firewall.add_time, width: 150 },
				{
					title: lan.public.operate,
					type: 'group',
					width: 150,
					align: 'right',
					group: [{
						title: lan.public.edit,
						event: function (row, index) {
							that.editIpRule(row)
						}
					}, {
						title: lan.public.del,
						event: function (row, index) {
							that.removeIpRule(row)
						}
					}]
				}]
		})
		return ruleTable;
	},
	/**
	 * @description 编辑ip规则
	 * @param { object } row 行数据
	 */
	editIpRule: function (row){
		var isEdit = !!row, that = this;
		row = row || {types:'drop',address:'',brief:''}
		layer.open({
			type: 1,
			area: '430px',
			title: (!isEdit ? lan.public.add : lan.public.edit) + lan.security.firewall.ip.form_title,
			closeBtn: 2,
			shift: 5,
			shadeClose: false,
			btn: [lan.public.confirm, lan.public.cancel],
			content: '<form id="editIpRuleForm" class="bt-form bt-form pd20" onsubmit="return false"></form>',
			yes:function(index,layers){
				bt_tools.verifyForm('#editIpRuleForm',[
					{
						name: 'address',
						validator: function (value, row) {
							if (!value) return lan.security.firewall.ip.form_ip
						}
					},
				], function (verify, form) {
					if(verify){
						// 添加、修改
						bt_tools.send({
							url:'/safe/firewall/' + (isEdit?'modify_ip_rules':'create_ip_rules'),
							data:{data:JSON.stringify($.extend({id:row.id},form))}
						}, function (rdata) {
							bt.msg(rdata)
							if(rdata.status){
								layer.close(index)
								that.ipRuleTable()
								that.getFirewallInfo()
							}
						}, (isEdit ? lan.public.editing : lan.public.adding) + lan.security.firewall.ip.form_title);
					}
				})
			},
			success:function(layero,index){
				bt_tools.fromGroup('#editIpRuleForm',[
					{
						label: lan.security.firewall.source_ip,
						name: 'address',
						type: 'textarea',
						readonly: isEdit,
						style: 'width: 220px; height: 80px; line-height: 22px;' + (isEdit ? 'background-color: rgb(238, 238, 238); cursor: not-allowed' : ''),
						placeholder: 'Please enter IP e.g. 192.168.1.102',
					},
					{
						label: lan.security.firewall.strategy,
						width: '220px',
						name: 'types',
						type: 'select',
						options: [
							{ value: 'accept', label: lan.security.firewall.release },
							{ value: 'drop', label: lan.security.firewall.block },
						],
					},
					{ label: lan.security.firewall.remarks, width: '220px', name: 'brief' },
					!isEdit
						? {
								type: 'tips',
								style: 'padding-left: 40px; margin-top:5px;',
								list: [
									lan.security.firewall.ip.form_tips1, 
									lan.security.firewall.ip.form_tips2, 
									lan.security.firewall.ip.form_tips3
								],
							}
						: { type: 'tips', list: [] },
				], row)
				bt_tools.setLayerArea(layero)
			}
		})
	},
	/**
	 * @description 删除端口规则
	 */
	removeIpRule:function(row){
		var that = this;
		bt.confirm({
			title: lan.security.firewall.ip.del_tit + ' ['+ row.address + ']',
			msg: lan.security.firewall.ip.del_msg 
		}, function () {
			bt_tools.send({ url:'/safe/firewall/remove_ip_rules', data:{data:JSON.stringify(row)}},function (rdata){
				bt.msg(rdata)
				if(rdata.status) {
					that.ipRuleTable()
					that.getFirewallInfo()
				}
			}, lan.security.firewall.ip.del_req);
		});
	},
	/**
	 * @description 端口转发列表
	 */
	portForwardTable: function () {
		var that = this;
		var forwardTable = bt_tools.table({
			el: '#portForward',
			url: '/safe/firewall/get_forward_list',
			load: lan.security.firewall.forward.load,
			default: lan.security.firewall.forward.default, // 数据为空时的默认提示
			autoHeight: true,
			beforeRequest: 'model',
			tootls: [
				{ // 按钮组
					type: 'group',
					list: [{
						title: lan.security.firewall.forward.add_btn,
						active: true,
						event: function (ev) {
							that.editPortForward()
						}
					}, {
						title: lan.security.firewall.import_btn,
						event: function (ev) {
							that.ruleImport('trans_rule')
						}
					}, {
						title: lan.security.firewall.export_btn,
						event: function (ev) {
							that.ruleExport('trans_rule')
						}
					}]
				},
				{ // 搜索内容
					type: 'search',
					placeholder: lan.security.firewall.forward.search,
					searchParam: 'query', //搜索请求字段，默认为 search
				},
				{
					type: 'batch', // 批量操作
					disabledSelectValue: lan.firewall.batch_disabled_tips('port forward'),
					placeholder: 'Select batch operation',
          buttonValue: 'Execute',
					selectList: [
						{
							title: lan.firewall.batch_del_btn('port forward'),
							url: '/safe/firewall/remove_forward',
							load: true,
							param: function (row) {
								return {
									data: JSON.stringify({ id: row.id, protocol: row.protocol, s_port: row.start_port, d_ip: row.ended_ip, d_port: row.ended_port }),
								};
							},
							refresh: true,
							callback: function (that) {
								bt.confirm({ title: lan.firewall.batch_del_title('port forward'), msg: lan.firewall.batch_del_msg_port_forward }, function () {
									var param = {};
									that.start_batch(param, function (list) {
										var html = '';
										for (var i = 0; i < list.length; i++) {
											var item = list[i];
											html +=
												'<tr><td>Source port: ' +
												item.start_port +
												'</td><td><div style="float:right;"><span style="color:' +
												(item.request.msg.indexOf('Success') > -1 ? '#20a53a' : 'red') +
												'">' +
												item.request.msg +
												'</span></div></td></tr>';
										}
										forwardTable.$batch_success_table({ title: lan.firewall.batch_del_title('IP'), th: 'Source port', html: html });
										forwardTable.$refresh_table_list(true);
										safety.getFirewallInfo();
									});
								});
							},
						},
					],
				},
				{ //分页显示
					type: 'page',
					numberStatus: true, //　是否支持分页数量选择,默认禁用
					jump: true, //是否支持跳转分页,默认禁用
				}
			],
			column: [
				{type: 'checkbox',  width: 20},
				{ title: lan.security.firewall.protocol, fid: 'protocol', width: 100 },
				{ title: lan.security.firewall.source_port, fid: 'start_port' },
				{
					title: lan.security.firewall.target_ip,
					fid: 'ended_ip', 
					template: function (row) {
						return '<span>'+ (row.ended_ip ? row.ended_ip : '127.0.0.1') +'</span>'
					}
				},
				{ title: lan.security.firewall.target_port, fid: 'ended_port' },
				{ title: lan.security.firewall.add_time, fid: 'addtime', width: 150 },
				{
					title: lan.public.operate,
					type: 'group',
					width: 150,
					align: 'right',
					group: [{
						title: lan.public.edit,
						event: function (row, index) {
							that.editPortForward(row)
						}
					}, {
						title: lan.public.del,
						event: function (row, index) {
							that.removePortForward(row)
						}
					}]
				}],
		});
		return forwardTable;
	},
	/**
	 * @description 添加/修改端口转发
	 * @param row
	 */
	editPortForward: function (row) {
		var isEdit = !!row, that = this;
		row = row || { protocol:'tcp', s_ports:'',d_address:'',d_ports:'' }
		layer.open({
			type: 1,
			area: "420px",
			title: (!isEdit ? lan.public.add : lan.public.edit) + lan.security.firewall.forward.form_title,
			closeBtn: 2,
			shift: 5,
			shadeClose: false,
			btn: [lan.public.import, lan.public.cancel],
			content: '<form id="editIpRuleForm" class="bt-form bt-form pd20" onsubmit="return false"></form>',
			yes:function(index,layers){
				bt_tools.verifyForm('#editIpRuleForm',[
					{name:'s_ports',validator:function (value,row){
							if(!value) return lan.security.firewall.source_port_val1
							if(!bt.check_port(value)) return lan.security.firewall.source_port_val2
						}},
					{name:'d_ports',validator:function (value,row){
							if(!value) return lan.security.firewall.target_port_val1
							if(!bt.check_port(value)) return lan.security.firewall.target_port_val2
						}},
				],function(verify,form){
					if(verify){
						// 添加、修改
						if(form['d_address'] === '') form['d_address'] = '127.0.0.1'
						bt_tools.send({
							url:'/safe/firewall/' + (isEdit?'modify_forward':'create_forward'),
							data:{data:JSON.stringify($.extend({id:row.id},form))}
						}, function (rdata) {
							bt.msg(rdata)
							if(rdata.status){
								layer.close(index)
								that.portForwardTable()
								that.getFirewallInfo()
							}
						},(isEdit ? lan.public.editing : lan.public.adding) + lan.security.firewall.forward.form_title);
					}
				})
			},
			success:function(layero,index){
				if(typeof row.id !== 'undefined') row = {s_ports:row.start_port,d_address:row.ended_ip,d_ports:row.ended_port,protocol:row.protocol,id:row.id}
				bt_tools.fromGroup('#editIpRuleForm', [
					{
						label: lan.security.firewall.protocol,
						width: '200px',
						name: 'protocol',
						type: 'select',
						options: [
							{ value: 'tcp', label: 'TCP' },
							{ value: 'udp', label: 'UDP' },
							{ value: 'tcp/udp', label: 'TCP/UDP' },
						],
					},
					{ label: lan.security.firewall.source_port, width: '200px', name: 's_ports', type: 'text', placeholder: lan.security.firewall.source_port_input },
					{ label: lan.security.firewall.target_ip, width: '200px', name: 'd_address', placeholder: lan.security.firewall.target_ip_input },
					{ label: lan.security.firewall.target_port, width: '200px', name: 'd_ports', type: 'text', placeholder: lan.security.firewall.target_port_input },
					{ type: 'tips', style: 'padding-left: 30px; margin-top:5px;', list: [lan.security.firewall.forward.form_tips1, lan.security.firewall.forward.form_tips2] },
				], row)
				bt_tools.setLayerArea(layero)
			}
		})
	},
	/**
	 * @description 删除端口转发
	 * @param {object} row 当前行数据
	 */
	removePortForward: function (row) {
		var that = this;
		bt.confirm({ 
			msg: lan.security.firewall.forward.del_msg, 
			title: lan.security.firewall.forward.del_tit + ' [' + lan.security.firewall.source_port + ': ' + row.start_port + ' -> ' + lan.security.firewall.target_port + ': ' + row.ended_port +']',
			area: '530px'
		}, function () {
			bt_tools.send({
				url:'/safe/firewall/remove_forward',
				data:{data:JSON.stringify({id:row.id,protocol:row.protocol,s_port:row.start_port,d_ip:row.ended_ip,d_port:row.ended_port})}
			}, function (rdata) {
				bt.msg(rdata);
				if(rdata.status) {
					that.portForwardTable();
					that.getFirewallInfo();
				}
			}, lan.security.firewall.forward.del_req);
		});
	},
	/**
	 * @description 国家区域
	 */
	countryRegionTable: function () {
		var that = this;
		var cRegionTable = bt_tools.table({
			el: '#countryRegion',
			url: '/safe/firewall/get_country_list',
			load: lan.security.firewall.area.load,
			default: lan.security.firewall.area.default, // 数据为空时的默认提示
			autoHeight: true,
			beforeRequest: 'model',
			column: [
				{type: 'checkbox', class: '', width: 20},
				{fid: 'country', title: lan.security.firewall.areas, width: 180,
					template:function (row){
						return '<span>'+ row.country + '(' + row.brief + ')</span>'
					}
				},
				{
					fid: 'types',
					title: lan.security.firewall.strategy,
					width: 100,
					template: function (row) {
						return row.types === 'accept'?'<span class="bt_success">' + lan.security.firewall.release + '</span>':'<span class="bt_danger">' + lan.security.firewall.block + '</span>'
					}
				},
				{fid: 'ports', title: lan.security.firewall.ports, template:function (row){
						return '<span>' + (!row.ports ? lan.security.firewall.all : row.ports) + '</span>'
					}},
				{fid: 'addtime', title: lan.security.firewall.add_time, width:150},
				{
					title: lan.public.operate,
					type: 'group',
					width: 150,
					align: 'right',
					group: [{
						title: lan.public.edit,
						event: function (row, index) {
							that.editCountryRegion(row);
						}
					}, {
						title: lan.public.del,
						event: function (row, index) {
							that.removeCountryRegion(row);
						}
					}]
				}],
			tootls: [
				{ // 按钮组
					type: 'group',
					list: [{
						title: lan.security.firewall.area.add_btn,
						active: true,
						event: function (ev) {
							that.editCountryRegion()
						}
					}, {
						title: lan.security.firewall.import_btn,
						event: function (ev) {
							that.ruleImport('country_rule')
						}
					}, {
						title: lan.security.firewall.export_btn,
						event: function (ev) {
							that.ruleExport('country_rule')
						}
					}]
				},
				{ // 搜索内容
					type: 'search',
					placeholder: lan.security.firewall.area.search,
					searchParam: 'query', //搜索请求字段，默认为 search
				},
				{
				  type: 'batch', // 批量操作
					disabledSelectValue: lan.firewall.batch_disabled_tips('area rule'),
					placeholder: 'Select batch operation',
          buttonValue: 'Execute',
					selectList: [
						{
							title: lan.firewall.batch_del_btn('area rule'),
							url: '/safe/firewall/remove_country',
							param: function (row) {
								return {
									data: JSON.stringify(row),
								};
							},
							refresh: true,
							load: true,
							callback: function (that) {
								bt.confirm({ title: lan.firewall.batch_del_title('area rule'), msg: lan.firewall.batch_del_msg_area_rule }, function () {
									var param = {};
									that.start_batch(param, function (list) {
										var html = '';
										for (var i = 0; i < list.length; i++) {
											var item = list[i];
											html +=
												'<tr><td>' +
												item.country +
												'</td><td><div style="float:right;"><span style="color:' +
												(item.request.msg.indexOf('Success') > -1 ? '#20a53a' : 'red') +
												'">' +
												item.request.msg +
												'</span></div></td></tr>';
										}
										cRegionTable.$batch_success_table({ title: lan.firewall.batch_del_title('area rule'), th: 'Area', html: html });
										cRegionTable.$refresh_table_list(true);
										safety.getFirewallInfo();
									});
								});
							},
						},
					],
				},
				{ //分页显示
					type: 'page',
					numberStatus: true, //　是否支持分页数量选择,默认禁用
					jump: true, //是否支持跳转分页,默认禁用
				}
			]
		})
		return cRegionTable;
	},

	/**
	 * @description 添加/修改端口转发
	 * @param row
	 */
	editCountryRegion:function (row) {
		var isEdit = !!row, that = this;
		row = row || { country: 'USA', types:'drop',brief:'US',ports:'' }
		bt_tools.send({
			url:'/safe/firewall/get_countrys',
		},  function (rdata) {
			layer.open({
				type: 1,
				area:"420px",
				title: (!isEdit ? lan.public.add : lan.public.edit) + lan.security.firewall.area.form_title,
				closeBtn: 2,
				shift: 5,
				shadeClose: false,
				btn: [lan.public.confirm, lan.public.cancel],
				content: '<form id="editCountryRegionForm" class="bt-form bt-form pd20" onsubmit="return false"></form>',
				yes: function (index, layers) {
					bt_tools.verifyForm('#editCountryRegionForm', [
						{
							name: 'ports',
							validator: function (value, row) {
								if (!value && row.choose !== 'all') return lan.security.firewall.specify_port_val1;
							}
						},
					], function (verify, form) {
						if (verify) {
							// 添加、修改
							form['brief'] = form.country;
							form['country'] = $('[name="country"]').find(':selected').text();
							if (form.choose === 'all') form.ports = '';
							bt_tools.send({
								url: '/safe/firewall/' + (isEdit ? 'modify_country' : 'create_country'),
								data: { data: JSON.stringify($.extend({ id: row.id }, form)) }
							}, function (rdata) {
								bt.msg(rdata)
								if(rdata.status){
									layer.close(index)
									that.countryRegionTable()
									that.getFirewallInfo()
								}
							}, (isEdit ? lan.public.editing : lan.public.adding) + lan.security.firewall.area.form_title);
						}
					})
				},
				success: function (layero, index) {
					var options = [];
					for (var i = 0; i < rdata.length; i++) {
						var item = rdata[i]
						options.push({
							label: item.CH,
							value: item.brief
						})
					}
					bt_tools.fromGroup('#editCountryRegionForm', [
						{ label: lan.security.firewall.areas, width: '200px', name: 'country', type: 'select', options: options },
						{ label: lan.security.firewall.strategy, width: '200px', name: 'types', type: 'select', options: [{ value:'drop', label: lan.security.firewall.block }] },
						{
							label: lan.security.firewall.ports,
							width: '200px',
							name: 'choose',
							type: 'select',
							options:[
								{ value: 'all', label: lan.security.firewall.all },
								// { value: 'point', label: lan.security.firewall.specify_port }
							], 
							on: {
								change: function (ev, val) {
									$(this).data('line').next().toggle()
								}
							}
						},
						{ label: '', width: '200px', name: 'ports', labelStyle: 'display:none', type: 'text', placeholder: lan.security.firewall.specify_port_input },
						{
							type:'tips',
							list:[
								lan.security.firewall.area.form_tips1,
								lan.security.firewall.area.form_tips2,
								lan.security.firewall.area.form_tips3
							],
							style: 'padding-left: 20px; margin-top:5px;'
						}
					], {
						country: row.brief,
						types: 'drop',
						choose: 'all'
					});
					if (row.ports) {
						$('select[name="choose"]').val('point');
						$('select[name="choose"]').change();
						$('input[name="ports"]').val(row.ports);
					}
					bt_tools.setLayerArea(layero);
				}
			});
		}, lan.security.firewall.area.get_area);
	},

	/**
	 * @description 删除地区规则
	 * @param {object} row 当前行数据
	 */
	removeCountryRegion: function (row) {
		var that = this;
		bt.confirm({
			msg: lan.security.firewall.area.del_msg, 
			title: lan.security.firewall.area.del_tit 
		}, function(){
			bt_tools.send({
				url:'/safe/firewall/remove_country',
				data:{data:JSON.stringify(row)}
			}, function (rdata) {
				bt.msg(rdata)
				if(rdata.status) {
					that.countryRegionTable()
					that.getFirewallInfo()
				}
			}, lan.security.firewall.area.del_req)
		});
	},
}

// ssh管理
var ssh = {
	init: function () {
		$('.state-content').show();
		$('.state-content .ssh-header').show();

		$('#sshView .tab-nav-border span').eq(0).trigger('click');
	},
	event: function () {
		var that = this;
		// 切换系统防火墙菜单事件
		$('#sshView').unbind('click').on('click', '.tab-nav-border span', function () {
			var index = $(this).index();
			$(this).addClass('on').siblings().removeClass('on');
			$(this).parent().next().find('.tab-block').eq(index).addClass('on').siblings().removeClass('on');
			$('.state-content').show().find('.ssh-header').show().siblings().hide();
			that.cutSshTab(index);
		});

		// SSH开关
		$('#isSsh').unbind('click').on('click',function(){
			var _that = $(this), status = _that.prop("checked") ? 0 : 1;
			bt.firewall.set_mstsc_status(status, function (rdata) {
				if(rdata === -1){
					_that.prop("checked",!!status);
				}else{
					bt.msg(rdata);
					that.getSshInfo();
				}
			});
		});

		// 保存SSH端口
		$('.save_ssh_port').unbind('click').on('click',function (){
			var port = $(this).prev().val();
			if(port === '') return bt.msg({ msg: lan.security.ssh.port_empty, icon: 2 });
			if(!bt.check_port(port)) return bt.msg({
				icon: 2,
				time: 0,
				closeBtn: 2,
				area: '400px',
				msg: lan.security.ssh.port_error1 + '<br />' + lan.security.ssh.port_error2 + '<br />[80, 443, 8080, 8443, 8888]',
			});
			bt.firewall.set_mstsc(port);
		});

		// root登录
		$('[name="root_login"]').unbind('change').on('change',function(){
			// var _that = $(this), status = _that.prop("checked");
			var root_type = $(this).val();
			bt_tools.send({
				url:'/ssh_security?action=set_root',
				data:{p_type:root_type}
			},function (rdata){
				bt_tools.msg(rdata);
			}, lan.security.ssh.set_root_req);
		});

		// SSH密码登录
		$('[name="ssh_paw"]').unbind('click').on('click',function (){
			var _that = $(this), start = _that.prop("checked");
			bt_tools.send({
				url:'/ssh_security?action=' + (start?'set_password':'stop_password')
			},function (rdata){
				bt_tools.msg(rdata);
			}, lan.security.ssh.set_paw_req);
		});

		// SSH密钥登录
		$('[name="ssh_pubkey"]').unbind('click').on('click',function(){
			var _that = $(this);
			var start = _that.prop("checked");
			if(start){
				that.setTemplateSshkey();
			}else{
				bt_tools.send({
					url:'/ssh_security?action=stop_key'
				},function (rdata){
					that.getSeniorSshInfo();
					bt_tools.msg(rdata);
				}, lan.security.ssh.set_pubkey_req);
			}
		});

		// 登录告警
		$('[name="ssh_login_give"]').unbind('click').on('click',function(){
			var _that = $(this), status = _that.prop("checked");
			bt_tools.send({
				url:'/ssh_security?action=' + (status?'start_jian':'stop_jian')
			},function (rdata){
				bt_tools.msg(rdata);
			}, lan.security.ssh.set_alarm_req);
		});

		// 查看密钥
		$('.checkKey').unbind('click').on('click',function (){
			that.setSshKeyView()
		});

		// 设置登录告警
		$('.setSshLoginAlarm').unbind('click').on('click',function (){
			that.setSshLoginAlarmView();
		});

		// 下载密钥
		$('.downloadKey').unbind('click').on('click',function (){
			bt_tools.send({
				url:'/ssh_security?action=get_key'
			},function (rdata){
				if(!rdata.msg) return layer.msg(lan.security.ssh.download_key_tips);
				window.open('/ssh_security?action=download_key')
			})
		});

		// 登录详情
		$('#sshDetailed').unbind('click').on('click','a',function (){
			var index = $(this).data('index');
			$('#sshView .tab-nav-border>span').eq(1).trigger('click');
			$('.cutLoginLogsType button').eq(index).trigger('click');
		});

		// 切换系统防火墙菜单事件
		$('#sshView').unbind('click').on('click', '.tab-nav-border span', function () {
			var index = $(this).index();
			that.cutSshTab(index);
    });

		// 切换登录日志类型
		$('#loginLogsContent').unbind('click').on('click','.cutLoginLogsType button',function(){
			var type = $(this).data('type');
			$(this).addClass('btn-success').removeClass('btn-default').siblings().addClass('btn-default').removeClass('btn-success');
			$('#loginLogsContent>div:eq('+ type +')').show().siblings().hide();
			that.loginLogsTable({p:1,type: Number(type)});
		});
	},
	cutSshTab: function (index) {
		switch (index){
			case 0:
				this.getSshInfo();
				this.getLoginAlarmInfo();
				this.getSeniorSshInfo();
				this.getSshLoginAlarmInfo();
				break;
			case 1:
				this.loginLogsTable();
				break;
		}
	},
	/**
	 * @description 获取SSH信息
	 */
	getSshInfo:function (load){
		bt_tools.send({
			url: '/safe/ssh/GetSshInfo',
			verify: false
		},function (rdata){
			var error = rdata.error;
			$('#sshDetailed .btlink').text(lan.security.ssh.success + ': '+ error.success);
			$('#sshDetailed .bterror').text(lan.security.ssh.fail + ': '+ error.error);
			$('#isSsh').prop("checked", rdata.status);
			$('[name="ssh_port"]').val(rdata.port);
		}, lan.security.ssh.get_ssh_info);
	},
	/**
	 * @description 获取登录告警信息
	 */
	getLoginAlarmInfo:function(load){
		bt_tools.send({
			url:'/ssh_security?action=get_jian'
		},function (rdata){
			$('#ssh_login_give').prop('checked', rdata.status);
		},  {load: load ? lan.security.ssh.get_jian : '',verify:false})
	},
	/**
	 * @description 获取高级SSH信息
	 */
	getSeniorSshInfo:function (load){
		bt_tools.send({
			url: '/ssh_security?action=get_config',
			verify: false
		},function (rdata){
			$('[name="ssh_paw"]').prop("checked",rdata.password === 'yes');
			$('[name="ssh_pubkey"]').prop("checked",rdata.pubkey === 'yes');

			var root_option = '';
			$.each(rdata.root_login_types,function(k,v){
					root_option += '<option value="'+ k +'" '+(rdata.root_login_type == k?'selected':'')+'>'+ v +'</option>';
			})
			$('[name="root_login"]').html(root_option);
			// $('[name="root_login"]').prop("checked",rdata.root_is_login === 'yes')
		}, load ? lan.security.ssh.get_config : '');
	},

	/**
	 * @description 获取SSH登录告警
	 */
	getSshLoginAlarmInfo: function (load) {
		var that = this;
		bt_tools.send({
			url: '/ssh_security?action=get_login_send',
			verify: false
		}, function (send) {
			var data = that.msgPushData;
			if (!data || $.isEmptyObject(data)) {
				bt_tools.send({
					url: '/ssh_security?action=get_msg_push_list',
					verify: false
				}, function (msgData) {
					that.msgPushData = msgData
					that.renderLoginAlarmInfo(send);
				});
			} else {
				that.renderLoginAlarmInfo(send);
			}
		}, load ? lan.security.ssh.get_login_send : '');
	},
	/**
	 * @description 渲染SSH登录告警配置
	 */
	renderLoginAlarmInfo: function (send) {
		var data = this.msgPushData || {};
		var map = {}
		$.each(data, function (key, item) {
			if (key === 'sms') return
			map[key] = item.title
		});
		var key = send.msg;
		var title = map[key];
		if (send.status && title) {
			$('a.setSshLoginAlarm').removeClass('bt_warning').addClass('btlink');
			$('a.setSshLoginAlarm').text(title + ' ' + lan.security.ssh.configured);
		} else {
			$('a.setSshLoginAlarm').addClass('bt_warning').removeClass('btlink');
			$('a.setSshLoginAlarm').text(lan.security.ssh.not_configured);
		}
	},

	/**
	 * @description 登录日志
	 */
	loginLogsTable:function(param){
		if(!param) param = { p:1, type:0 };
		var logs = [
			['All', lan.security.ssh.logs, 'get_ssh_list'],
			['Success', lan.security.ssh.s_logs, 'get_ssh_success'],
			['Error', lan.security.ssh.f_logs, 'get_ssh_error']
		];
		var type = logs[param.type][0];
		var tips = logs[param.type][1];

		$('#login'+ type +'Logs').empty();
		var arry = [lan.security.ssh.all, lan.security.ssh.success, lan.security.ssh.fail];
		var html = $('<div class="btn-group mr10 cutLoginLogsType"></div>');
		$.each(arry,function (i,v){
			html.append('<button type="button" class="btn btn-sm btn-'+ (i === param.type ?'success':'default') +'" data-type="'+ i +'">'+ v +'</button>')
		});
		return bt_tools.table({
			el: '#login'+ type +'Logs',
			url: '/safe/syslog/' + logs[param.type][2],
			default: lan.security.ssh.get_ssh_list1 + tips + lan.security.ssh.get_ssh_list2, // 数据为空时的默认提示
			autoHeight: true,
			dataVerify:false,
			tootls: [
				{ // 按钮组
					type: 'group',
					list: [{
						title: lan.security.ssh.refresh,
						active: true,
						event: function (ev,that) {
							that.$refresh_table_list(true)
						}
					}]
				},
				{ // 搜索内容
					type: 'search',
					placeholder: lan.security.ssh.login_search,
					searchParam: 'search', //搜索请求字段，默认为 search
				},
				{ //分页显示
					type: 'page',
					number: 20
				}
			],
			dataFilter: function (data) {
				if ((typeof data.status === "boolean" && !data.status)) {
					$('#loginLogsContent').hide().next().show();
					return { data: [] }
				}
				return {data:data}
			},
			beforeRequest: function (data) {
				if(typeof data.data === "string"){
					delete data.data
					return {data: JSON.stringify(data)}
				}
				return {data: JSON.stringify(data)}
			},
			column: [
				{title: lan.security.ssh.ip_port,fid: 'address',width:'150px', template:function (row){
						return '<span>'+ row.address +':' + row.port + '</span>';
					}},
				// {title: '登录端口',fid: 'port'},
				{title: lan.security.ssh.place,template:function (row){
						return '<span>'+ (row.area?'' + row.area.info + '':'-') +'</span>';
					}},
				{title: lan.security.ssh.user,fid: 'user'},
				{title: lan.security.ssh.status, template: function (item) {
						var status = Boolean(item.status);
						return '<span style="color:'+ (status?'#20a53a;':'red') +'">'+ (status ? lan.security.ssh.l_success : lan.security.ssh.l_fail) +'</span>';
					}},
				{title: lan.security.ssh.o_time, fid: 'time', width:150}
			],
			success:function (config){
				$(config.config.el + ' .tootls_top .pull-right').prepend(html)
				$('#login'+ type +'Page').html(firewall.renderLogsPages(20,param.p,config.data.length))
			}
		});
	},
	/**
	 * @description 设置密钥登录
	 */
	setTemplateSshkey:function(){
		var _this = this;
		layer.open({
			title: lan.security.ssh.key_title,
			area: '430px',
			type: 1,
			closeBtn: 2,
			btn: [lan.public.confirm, lan.public.cancel],
			content:'<div class="bt-form bt-form pd20">'+
					'<div class="line"><span class="tname" style="width: 160px">' + lan.security.ssh.key_login + '</span><div class="info-r" style="margin-left: 160px"><select class="bt-input-text mr5 ssh_select_login" style="width:200px"><option value="yes">' + lan.security.ssh.enable + '</option><option value="no">' + lan.security.ssh.disable + '</option></select></div></div>'+
					'<div class="line "><span class="tname" style="width: 160px">' + lan.security.ssh.key_mode + '</span><div class="info-r" style="margin-left: 160px"><select class="bt-input-text mr5 ssh_select_encryption" style="width:200px"><option value="ed25519">ED25519(' + lan.security.ssh.recommend + ')</option><option value="ecdsa">ECDSA</option><option value="rsa">RSA</option><option value="dsa">DSA</option></select></div></div>'+
					'</div>',
			yes:function(indexs){
				var ssh_select_login = $('.ssh_select_login').val();
				var ssh_select_encryption = $('.ssh_select_encryption').val();
				bt_tools.send({
					url:'/ssh_security?action=set_sshkey',
					data:{ ssh:ssh_select_login, type:ssh_select_encryption }
				},function (rdata){
					bt_tools.msg(rdata);
					layer.close(indexs);
					_this.getSeniorSshInfo();
				}, lan.security.ssh.set_sshkey);
			},
			cancel:function(index){
				$('[name="ssh_pubkey"]').prop('checked',false);
			},
			btn2:function(index){
				$('[name="ssh_pubkey"]').prop('checked',false);
			}
		});
	},
	/**
	 * @description 设置SSH密钥视图
	 */
	setSshKeyView:function(){
		var _this = this
		bt_tools.send({
			url:'/ssh_security?action=get_key'
		},function (rdata){
			if (!rdata.msg) return layer.msg(lan.security.ssh.key_view_msg);
			layer.open({
				title: lan.security.ssh.key_view_title,
				area:'400px',
				type:1,
				closeBtn: 2,
				content:'<div class="bt-form pd20">\
					<textarea id="ssh_text_key" class="bt-input-text mb10" style="height:220px;width:360px;line-height: 22px;">'+ rdata.msg +'</textarea>\
					<div class="btn-sshkey-group">\
						<button type="button" class="btn btn-success btn-sm mr5 btn-copy-sshkey">' + lan.security.ssh.copy + '</button>\
						<button type="button" class="btn btn-default btn-sm mr5 btn-download-sshkey">' + lan.security.ssh.download + '</button>\
						<button type="button" class="btn btn-default btn-sm btn-rebuild-sshkey">' + lan.security.ssh.regenerate + '</button>\
					</div>\
				</div>',
				success:function (layers,indexs){
					$('.btn-copy-sshkey').on('click',function(){
						bt.pub.copy_pass($('#ssh_text_key').val());
					})
					$('.btn-download-sshkey').on('click',function(){
						window.open('/ssh_security?action=download_key')
					})
					$('.btn-rebuild-sshkey').on('click',function(){
						bt_tools.send({
							url:'/ssh_security?action=set_sshkey',
							data:{ ssh:'yes', type:'ed25519' }
						},function (res){
							bt_tools.send({
								url:'/ssh_security?action=get_key'
							},function (rdata){
								if(!rdata.msg) return layer.msg(lan.security.ssh.key_view_msg);
								$('#ssh_text_key').val(rdata.msg);
								if(res.status) bt_tools.msg({ msg: lan.security.ssh.get_key_msg, status: true });
								_this.getSeniorSshInfo();
							})
						}, lan.security.ssh.get_key);
					})
				}
			})
		}, lan.security.ssh.get_key_req);
	},
	/**
	 * @description 设置SSH登录告警
	 */
	setSshLoginAlarmView:function(){
		var that = this;
		layer.open({
			title: lan.security.ssh.alarm_title,
			area: '1010px',
			type: 1,
			closeBtn: 2,
			content: '\
			<div class="bt-w-main">\
				<div class="bt-w-menu">\
					<p class="bgw">' + lan.security.ssh.alarm_set + '</p>\
					<p>' + lan.security.ssh.ip_white + '</p>\
				</div>\
				<div class="bt-w-con pd15">\
					<div class="plugin_body">\
						<div class="content_box news-channel active">\
							<div class="bt-form-new inline"></div>\
							<div id="login_logs_table" class="divtable mt10">\
								<div style="width: 100%; border: 1px solid #ddd; overflow: auto;">\
									<table class="table table-hover" style="border: none;">\
										<thead>\
											<tr>\
												<th>' + lan.security.ssh.login_info + '</th>\
												<th class="text-right">' + lan.security.ssh.time + '</th>\
											</tr>\
										</thead>\
										<tbody>\
											<tr>\
												<td colspan="2" class="text-center">' + lan.site.data_empty + '</td>\
											</tr>\
										</tbody>\
									</table>\
								</div>\
								<div class="page"></div>\
							</div>\
							<ul class="help-info-text c7">\
								<li></li>\
							</ul>\
						</div>\
						<div class="content_box hide">\
							<div class="bt-form">\
								<div class="box" style="display:inline-block;">\
									<input name="ipAddress" class="bt-input-text mr5" type="text" style="width: 220px;" placeholder="' + lan.security.ssh.ip_white_input + '" />\
									<button class="btn btn-success btn-sm addAddressIp">' + lan.public.add + '</button>\
								</div>\
							</div>\
							<div id="whiteIpTable"></div>\
							<ul class="help-info-text c7">\
								<li style="list-style:inside disc">' + lan.security.ssh.ip_white_tips + '</li>\
							</ul>\
						</div>\
					</div>\
				</div>\
			</div>',
			success: function ($layer, indexs) {
				// layer
				var _that = this;

				// 切换菜单
				$layer.find('.bt-w-menu p').click(function () {
					var index = $(this).index();
					$(this).addClass('bgw').siblings('.bgw').removeClass('bgw');
					$layer.find('.content_box').addClass('hide');
					$layer.find('.content_box').eq(index).removeClass('hide');
					switch (index) {
						// 登录日志
						case 0:
							_that.renderAlarm();
							_that.renderLogsTable(1, false);
							break;
						// IP白名单
						case 1:
							_that.renderWhiteIpTable()
							break;
					}
				});

				// 设置告警通知
				$('.news-channel .bt-form-new').on('change', 'input[type="checkbox"]', function () {
					var $this = $(this);
					var name = $this.attr('name');
					var checked = $this.is(':checked');
					var action = checked ? 'set_login_send' : 'clear_login_send'
					bt_tools.send({
						url: '/ssh_security?action=' + action,
						data:{ type: name }
					}, function (rdata) {
						bt_tools.msg(rdata);
						if (rdata.status) {
							if (checked) {
								$('.news-channel .bt-form-new input[type="checkbox"]').prop('checked', false);
								$this.prop('checked', true);
							}
							that.getSshLoginAlarmInfo();
						} else {
							$this.prop('checked', !checked);
						}
					}, {
						verify: false,
						load: lan.security.ssh.login_send
					});
				});

				// 登录日志分页操作
				$('#login_logs_table .page').on('click', 'a', function (e) {
					e.stopPropagation();
					e.preventDefault();
					var page = $(this)
						.attr('href')
						.match(/p=([0-9]*)/)[1];
					_that.renderLogsTable(page);
				});

				// 添加ip
				$('.addAddressIp').click(function () {
					var address = $('[name="ipAddress"]');
					var ip = address.val();
					address.val('');
					if (!ip) {
						bt_tools.msg({ msg: lan.security.ssh.ip_white_input, status: false });
						return;
					}
					bt_tools.send({
						url:'/ssh_security?action=add_return_ip',
						data:{ ip: ip }
					}, function (rdata) {
						bt_tools.msg(rdata);
						_that.renderWhiteIpTable();
					}, lan.security.ssh.add_return_ip);
				});

				$layer.find('.bt-w-menu p').eq(0).click();
			},
			// 生成告警
			renderAlarm: function () {
				// 获取告警列表
				bt_tools.send({
					url: '/ssh_security?action=get_msg_push_list',
				}, function (alarms) {
					// 获取选中告警
					bt_tools.send({
						url: '/ssh_security?action=get_login_send',
					}, function (send) {
						var html = '';
						var tits = [];
						// 当前选中的告警key
						var cKey = send.msg;
						// 渲染生成告警列表
						$.each(alarms, function (key, item) {
							if (item.name === 'sms') return;
							var checked = cKey === item.name ? 'checked="checked"' : '';
							html += '\
							<div class="form-item">\
								<div class="form-label">Send to ' + item.title + '</div>\
								<div class="form-content">\
									<input type="checkbox" id="' + item.name + '_alarm" class="btswitch btswitch-ios" ' + checked + ' name="' + item.name + '" />\
									<label class="btswitch-btn" for="' + item.name + '_alarm"></label>\
								</div>\
							</div>';
							tits.push(item.title);
						});
						$('.news-channel .bt-form-new').html(html);
						$('.news-channel .help-info-text li').eq(0).text('Only one of the above options can be enabled simultaneously');
					});
				}, lan.security.ssh.get_msg_push_list);
			},
			// 生成日志表格
			renderLogsTable: function (p, load) {
				p = p || 1;
				load = load !== undefined ? load : true;
				if (load) var loadT = bt_tools.load(lan.security.ssh.get_logs);
				bt_tools.send({
					url: '/ssh_security?action=get_logs',
					data: { p: p, p_size: 8, }
				}, function (rdata) {
					if (load) loadT.close();
					var html = '';
					if (rdata.data) {
						for (var i = 0; i < rdata.data.length; i++) {
							var item = rdata.data[i];
							html += '<tr><td style="white-space: nowrap;" title="' + item.log + '">' + item.log + '</td><td class="text-right">' + item.addtime + '</td></tr>';
						}
					}
					html = html || '<tr><td class="text-center">' + lan.site.data_empty + '</td></tr>';
					$('#login_logs_table table tbody').html(html);
					$('#login_logs_table .page').html(rdata.page || '');
				});
			},
			// 生成IP白名单表格
			renderWhiteIpTable: function () {
				var _that = this;
				if (this.ipTable) {
					this.ipTable.$refresh_table_list();
					return;
				}
				this.ipTable = bt_tools.table({
					el: '#whiteIpTable',
					url: '/ssh_security?action=return_ip',
					autoHeight: true,
					height: '425px',
					default: lan.security.ssh.return_ip_default,
					dataFilter: function (data) {
						return { data: data.msg };
					},
					column: [
						{
							title: 'IP',
							template: function (item) {
								return '<span>'+ item + '</span>';
							}
						},
						{
							title: lan.public.operate,
							type: 'group',
							width: 150,
							align: 'right',
							group: [
								{
									title: lan.public.del,
									event: function (row, index) {
										bt_tools.send({
											url: '/ssh_security?action=del_return_ip',
											data: { ip: row }
										},function (rdata){
											bt_tools.msg(rdata)
											_that.renderWhiteIpTable();
										}, lan.security.ssh.del_return_ip);
									}
								}
							]
						}
					]
				});
			}
		});
	}
}

// 入侵防御
var intrusion = {
	init: function () {
		$('.state-content').hide();

		bt.soft.get_soft_find('bt_security', function (rdata) {
			// 判断插件未安装 && 插件是否过期
			if (!rdata.setup && rdata.endtime > -1) {
				$('.buyIntrusion').hide();
			}
			// 判断插件已安装 && 插件是否过期
			if ((rdata.setup && rdata.endtime > -1)) {
				$('.state-content').show();
				$('.state-content .intrusion-header').show();
				$('#intrusion .installSoft').hide();
				$('#intrusion .tab-nav-border, #intrusion .tab-nav-con').show();
				$('#intrusion .tab-nav-border span').eq(0).trigger('click');
			} else {
				$('.state-content').hide();
				$('#intrusion .installSoft').show();
				$('#intrusion .tab-nav-border,#intrusion .tab-nav-con').hide();

				if (rdata.endtime > -1) {
					$('.purchaseIntrusion').hide();
				}else{
					$('.installIntrusion').hide();
				}
			}
		});
	},
	event: function () {
		var that = this;
		
		// 切换系统防火墙菜单事件
		$('#intrusion').on('click', '.tab-nav-border span', function () {
			var index = $(this).index();
			that.cutSshTab(index);
		});
		$('#isIntrusion').unbind('click').on('click', function () {
			var status = $(this).prop('checked');
			that.setIntrusionSwitch(status);
		});
		$('.installSoft .thumbnail-tab li').on('click',function(){
			var index = $(this).index();
			$(this).addClass('on').siblings().removeClass('on');
			$('.installSoft .thumbnail-item').eq(index).addClass('show').siblings().removeClass('show');
		});
		$('.installIntrusion').on('click', function (){
			bt.soft.install('bt_security', function (rdata) {
				location.reload();
			});
		});
		$('.purchaseIntrusion').on('click', function () {
			bt.soft.updata_ltd(true);
		});
	},
	/**
     * @description 切换SSH管理页面
     */
	cutSshTab:function (index){
		switch (index){
			case 0:
				this.overviewList();
				break;
			case 1:
				this.processWhiteList();
				break;
			case 2:
				this.interceptLog();
				break;
			case 3:
				this.operationLog();
				break;
		}
	},

	/**
	 * @description 设置防入侵开关
	 */
	setIntrusionSwitch:function (status){
		bt_tools.send({
			url:'/plugin?action=a&name=bt_security&s='+ (status?'start_bt_security':'stop_bt_security'),
		},function(rdata){
			bt_tools.msg(rdata);
		}, lan.security.intrusion.switch_req);
	},

	/**
	 * @description 概览列表
	 */
	overviewList:function () {
		var _that = this;
		return bt_tools.table({
			el: '#antiOverviewList',
			url: '/plugin?action=a&name=bt_security&s=get_total_all',
			load: lan.security.intrusion.overview_req,
			default: lan.security.intrusion.overview_default, // 数据为空时的默认提示
			autoHeight: true,
			height: '450px',
			dataFilter: function (data) {
				$('#isIntrusion').prop('checked', data.open);
				$('.totlaDays').html(data.totla_times).css(data.totla_times ? { 'color': '#d9534f', 'font-weight': 'bold' } : {});
				$('.totlaTimes').html(data.totla_days).css(data.totla_days ? { 'color': '#d9534f', 'font-weight': 'bold' } : {});
				return { data: data.system_user };
			},
			column: [
				{title: lan.security.intrusion.user, fid: '0'},
				{title: lan.security.intrusion.total,align: 'center', template:function (row){
						var total = row[4].totla;
						return '<span class="'+ (total > 0?'bt_danger':'') +'">'+ total + '</span>';
					}},
				{title: lan.security.intrusion.today, align: 'center', template:function (row){
						var today = row[4].day_totla;
						return '<span class="'+ (today > 0?'bt_danger':'') +'">'+ today + '</span>';
					}},
				{
					title: lan.security.intrusion.protection,
					fid:'3',
					type: 'switch',
					event: function (row, index, ev, key, that) {
						bt_tools.send({
							url:'/plugin?action=a&name=bt_security&s='+(row[3]?'stop_user_security':'start_user_security'),
							data:{ user: row[0] }
						},function (rdata){
							bt_tools.msg(rdata);
							that.$refresh_table_list();
						}, function (rdata) {
							bt_tools.msg(rdata);
							$(ev.currentTarget).prop('checked', row[3]);
						}, lan.security.intrusion.protection_req);
					}
				},
				{
					title: lan.security.intrusion.log,
					fid:'5',
					type: 'switch',
					event: function (row, index, ev, key, that) {
						bt_tools.send({
							url:'/plugin?action=a&name=bt_security&s='+(row[5]?'stop_user_log':'start_user_log'),
							data:{ uid:row[1] }
						},function (rdata){
							bt_tools.msg(rdata);
							that.$refresh_table_list();
						}, lan.security.intrusion.log_req);
					}
				},
				{title: lan.security.intrusion.remark, fid:'6'},
				{
					title: lan.public.operate,
					type: 'group',
					width: 150,
					align: 'right',
					group: [{
						title: lan.security.intrusion.logs,
						event: function (row, index) {
							_that.getCmdLogs(row)
						}
					}]
				}
			]
		})
	},

	/**
	 * @description 获取命令日志
	 * @param {Object} row 当前行数据
	 */
	getCmdLogs:function (row){
		var that = this;
		bt_tools.send({
			url:'/plugin?action=a&name=bt_security&s=get_logs_list',
			data:{ user:row[0] }
		},function (rdata){
			if(rdata.length > 0){
				that.openLogsView(rdata,row[0]);
			}else{
				layer.msg(lan.security.intrusion.no_logs, { icon: 6 });
			}
		})
	},

	/**
	 * @description 打开日志视图
	 */
	openLogsView:function (arr,user){
		var that = this;
		layer.open({
			type: 1,
			title: "["+ user +"] - " + lan.security.intrusion.logs_title,
			area: ['840px', '570px'],
			closeBtn: 2,
			shadeClose: false,
			content: '<div class="logs-list-box pd15">\
			<div class="logs-data-select">\
					<div class="logs-title">' + lan.security.intrusion.select_date + ': </div>\
					<div class="logs-unselect">\
						<div class="logs-inputs"><div class="logs-inputs-tips">'+ arr[0] +'</div></div>\
						<dl class="logs-input-list" data-val="'+ arr[0] +'"></dl>\
					</div>\
			</div>\
			<div class="logs-table bt-table">\
					<div id="logsTable"></div>\
					<div class="logs-page page-style pull-right page"></div>\
					</div>\
			</div>',
			success:function(layers,index){
				var _html = '';
				for(var i = 0;i<arr.length;i++){
					_html += '<dd logs-data="'+ arr[i] +'" '+ ( i === 0?'class="logs_checked"':'' ) +'>'+ arr[i] +'</dd>';
				}
				$('.logs-list-box .logs-input-list').html(_html);
				$('.logs-list-box .logs-inputs').on('click',function(e){
					if(!$(this).parent().hasClass('active')){
						$(this).parent().addClass('active');
					}else{
						$(this).parent().removeClass('active');
					}
					$(document).unbind('click').click(function(e){
						$('.logs-unselect').removeClass('active');
						$(this).unbind('click');
					});
					e.stopPropagation();
					e.preventDefault();
				});

				$('.logs-input-list dd').on('click',function(e){
					var _val = $(this).attr('logs-data');
					$(this).addClass('logs_checked').siblings().removeClass('logs_checked');
					$(this).parent().attr('data-val',_val);
					$(this).parent().prev().find('.logs-inputs-tips').html(_val);
					that.renderLogsTable({ page:1, day:_val, user:user});
				});

				$('.logs-page').unbind().on('click','a.nextPage',function(e){
					var _page = parseInt($(this).attr('data-page'));
					var _day = $('.logs-input-list dd').attr('logs-data');
					that.renderLogsTable({ page:_page, day:_day, user:user});
				});

				$('.logs-input-list dd:eq(0)').click();

			}
		})
	},

	/**
	 * @description 渲染日志视图
	 * @param {object} data 日志数据
	 */
	renderLogsTable:function (data){
		var _that = this, table = $('#logsTable'), dataTable = table.data('table');
		table.empty();
		return bt_tools.table({
			el: '#logsTable',
			url: '/plugin?action=a&name=bt_security&s=get_user_log',
			load: lan.security.intrusion.logs_req,
			default: lan.security.intrusion.logs_default, // 数据为空时的默认提示
			autoHeight: true,
			column: [
				{title: lan.security.intrusion.user, template:function (row) { return '<span>'+ data.user +'</span>' }},
				{title: lan.security.intrusion.user, fid: 'cwd'},
				{title: lan.security.intrusion.command_executed, fid: 'cmd'},
				{title: lan.security.intrusion.command_path, fid: 'filename'},
				{title: lan.security.intrusion.time,align:'right', template: function (row) {
						return '<span>'+ bt.format_data(row.timestamp) +'</span>';
					}}
			],
			beforeRequest: function (param) {
				return $.extend(param,{ p:data.page, day:data.day, user:data.user, num:11});
			},
			success: function (rdata) {
				$('.logs-page').html(firewall.renderLogsPages(10,data.page,rdata.data.length));
			}
		});
	},

	/**
	 * @description 进程白名单
	 */
	processWhiteList:function (){
		var _that = this;
		return bt_tools.table({
			el: '#antiProcessWhiteList',
			url: '/plugin?action=a&name=bt_security&s=porcess_set_up_log',
			load: lan.security.intrusion.whitelist_req,
			default: lan.security.intrusion.whitelist_default, // 数据为空时的默认提示
			autoHeight: true,
			dataFilter: function (data) {
				return {data:data};
			},
			tootls: [
				{ // 按钮组
					type: 'group',
					list: [{
						title: lan.security.intrusion.add_whitelist,
						active: true,
						event: function (ev) {
							bt.open({
								title: lan.security.intrusion.add_whitelist,
								area:'430px',
								btn: [lan.public.confirm, lan.public.cancel],
								content:'<div class="bt-form">\
										<div class="line">\
										<span class="tname" style="font-size: 12px;">' + lan.security.intrusion.process_name + '</span>\
											<div class="info-r"><input type="text" name="cmd" placeholder="' + lan.security.intrusion.process_name_input + '" class="bt-input-text mr10 " style="width:220px;" value="" /></div>\
										</div>\
									</div>\
									<ul class="help-info-text c7" style="margin: 5px 0 0 0;font-size: 12px;"><li style="color:red">' + lan.security.intrusion.add_whitelist_tips + '</li></ul>',
								yes:function (){
									var cmd = $('[name="cmd"]').val();
									bt_tools.send({
										url: '/plugin?action=a&name=bt_security&s=add_porcess_log',
										data: { cmd:cmd }
									},function (rdata){
										bt_tools.msg(rdata);
										_that.processWhiteList()
									})
								}
							})
						}
					}]
				},
				// { // 批量操作
				//   type: 'batch', //batch_btn
				//   disabledSelectValue: '请选择需要批量操作的站点!',
				//   selectList: [{
				//     title: "删除项目",
				//     url: '/project/nodejs/remove_project',
				//     param: function (row) {
				//       return { data: JSON.stringify({ project_name: row.name }) }
				//     },
				//     refresh: true,
				//     callback: function (that) {
				//
				//     }
				//   }
				//   ],
				// },
			],
			column: [
				{
					title: lan.security.intrusion.process_whitelist,
					template: function (row) {
						return '<span>'+ row + '</span>';
					}
				},
				{
					title: lan.public.operate,
					type: 'group',
					width: 150,
					align: 'right',
					group: [{
						title: lan.public.del,
						event: function (row, index) {
							console.log(arguments);
							bt.confirm({
								title: lan.security.intrusion.del_whitelist_title + ' ['+ row +']',
								msg: lan.security.intrusion.del_whitelist_msg
							}, function () {
								bt_tools.send({
									url:'/plugin?action=a&name=bt_security&s=del_porcess_log',
									data:{ cmd: row }
								},function (rdata){
									_that.processWhiteList()
									bt_tools.msg(rdata)
								})
							})
						}
					}]
				}
			]
		})
	},

	/**
	 * @description 拦截日志
	 */
	interceptLog:function (){
		var _that = this;
		return bt_tools.table({
			el: '#antiInterceptLog',
			url: '/plugin?action=a&name=bt_security&s=get_log_send',
			load: lan.security.intrusion.intercept_logs_req,
			default: lan.security.intrusion.intercept_logs_default, // 数据为空时的默认提示
			autoHeight: true,
			dataFilter: function (res) {
				return { data: res.data };
			},
			column: [
				{title: lan.security.intrusion.intercept_content, template:function (row){
						return '<span>'+ row.log + '</span>';
					}},
				{title: lan.security.intrusion.trigger_time, width:'170px', align: 'right', template:function (row){
						return '<span>'+ row.addtime + '</span>';
					}}
			]
		})
	},

	/**
	 * @description 操作日志
	 */
	operationLog:function (){
		var _that = this;
		return bt_tools.table({
			el: '#antiOperationLog',
			url: '/plugin?action=a&name=bt_security&s=get_log',
			load: lan.security.intrusion.operation_logs_req,
			default: lan.security.intrusion.operation_logs_default, // 数据为空时的默认提示
			autoHeight: true,
			tootls:[{ //分页显示
				type: 'page',
				jump: true, //是否支持跳转分页,默认禁用
			}],
			column: [
				{title: lan.public.operate, template:function (row){
						return '<span title="'+ row.log +'">'+ row.log + '</span>';
					}},
				{title: lan.security.intrusion.date, fid:'addtime', width:'170px'},
			]
		})
	}
}

// 系统加固
var system = {
	ipTable: null,
	init: function () {
		$('.state-content').show();
		$('.state-content .system-header').show();

		bt.soft.get_soft_find('syssafe', function (rdata) {
			// 判断插件未安装 && 插件是否过期
			if (!rdata.setup && rdata.endtime > -1) {
				$('.buySystem').hide();
			}
			// 判断插件已安装 && 插件是否过期
			if ((rdata.setup && rdata.endtime > -1)) {
				$('#system .tab-nav-border, #system .tab-nav-con').show();
				$('#system .installSoft').hide();
				$('#system .tab-nav-border span').eq(0).trigger('click');
			} else {
				$('#system .tab-nav-border, #system .tab-nav-con').hide();
				$('#system .installSoft').show();
				$('.state-content').hide();
				
				if (rdata.endtime > - 1) {
					$('.purchaseSystem').hide();
				} else {
					$('.installSystem').hide();
				}
			}
		});
	},
	/**
	 * @description SSH管理列表
	 */
	event: function () {
		var that = this;

		// 切换系统防火墙菜单事件
		$('#system').on('click', '.tab-nav-border span', function () {
			var index = $(this).index();
			that.cutSshTab(index);
		});

		// 系统加固开关
		$('#isReinforcement').unbind('change').change(function () {
			var $this = $(this)
			bt_tools.send({
				url: '/plugin?name=syssafe&action=a&s=set_open',
			}, function (rdata) {
				bt_tools.msg(rdata);
			}, function (rdata) {
				bt_tools.msg(rdata);
				var checked = $this.prop('checked');
				$this.prop('checked', !checked);
			}, lan.security.system.switch_req);
		});

		// 添加封锁ip地址
		$('.system_add_ip').click(function () {
			var $ip = $('input[name="system_address"]')
			var ip = $ip.val().trim();
			if (!ip) {
				$ip.focus();
				return layer.msg(lan.security.system.add_ip_val1, { icon: 2 });
			}
			if (!bt.check_ip(ip)) {
				$ip.focus();
				return layer.msg(lan.security.system.add_ip_val2, { icon: 2 });
			}
			bt_tools.send({
				url: '/plugin?name=syssafe&action=a&s=add_ssh_limit',
				data: { ip: ip }
			}, function (rdata) {
				bt_tools.msg(rdata);
				if (rdata.status) $ip.val('');
				that.getBlockIp();
			}, lan.security.system.add_ip_req);
		});

		$('#system .installSoft .thumbnail-tab li').unbind('click').on('click',function(){
			var index = $(this).index()
			$(this).addClass('on').siblings().removeClass('on')
			$('#system .installSoft .thumbnail-item').eq(index).addClass('show').siblings().removeClass('show')
		});

		$('.installSystem ').unbind('click').on('click',function (){
			bt.soft.install('syssafe',function (rdata) {
				location.reload();
			});
		});

		$('.purchaseSystem').unbind('click').on('click',function (){
			bt.soft.updata_ltd(true);
		});
	},

	/**
	 * @description 切换SSH管理页面
	 */
	cutSshTab:function (index){
		switch (index){
			case 0:
				this.reinforceSystem();
				break;
			case 1:
				this.reinforceBlockIp();
				break;
			case 2:
				this.reinforceLog();
				break;
		}
	},

	/**
	 * @description 渲染系统加固配置
	 */
	renderSafeConfig:function (){
		if (s_key === 'process') {
			system_reinforcement.process_config()
			return;
		}

		if (s_key === 'ssh') {
			system_reinforcement.ssh_config()
			return;
		}
		bt_tools.send({
			url: '/plugin?name=syssafe&action=a&s=get_safe_config',
			data: { s_key: s_key }
		},function (rdata){
			var chattrs = { "a": "追加", "i": "只读" }
			var states = { true: "<a style=\"color:green;\">已保护</a>", false:"<a style=\"color:red;\">未保护</a>" }
			var tbody = '';
			for (var i = 0; i < rdata.paths.length; i++) {
				tbody += '<tr>\
					<td>' + rdata.paths[i].path + '</td>\
					<td>' + chattrs[rdata.paths[i].chattr] + '</td>\
					<td>' + (rdata.paths[i].s_mode === rdata.paths[i].d_mode ? rdata.paths[i].s_mode:(rdata.paths[i].s_mode + ' >> ' + rdata.paths[i].d_mode)) + '</td>\
					<td>' + states[rdata.paths[i].state] + '</td>\
					<td style="text-align: right;"><a class="btlink" onclick="system_reinforcement.remove_safe_config(\''+ s_key + '\',\'' + rdata.paths[i].path + '\')">删除</a></td>\
				</tr>'
			}
			if (system_reinforcement.message_box_noe) {
				layer.close(system_reinforcement.message_box_noe);
				system_reinforcement.message_box_noe = null;
			}

			system_reinforcement.message_box_noe = layer.open({
				type: 1,
				title: "配置【" + rdata.name + "】",
				area: ['700px', '550px'],
				closeBtn: 2,
				shadeClose: false,
				content: '<div class="pd15">\
						<div style="border-bottom:#ccc 1px solid;margin-bottom:10px;padding-bottom:10px">\
						<input class="bt-input-text" name="s_path" id="s_path" type="text" value="" style="width:250px;margin-right:5px;" placeholder="被保护的文件或目录完整路径"><a class="glyphicon cursor glyphicon-folder-open" onclick="bt.select_path(\'s_path\')" style="color:#edca5c;margin-right:20px;font-size:16px"></a>\
						<select class="bt-input-text" name="chattr"><option value="i">只读</option><option value="a">追加</option></select>\
						<input class="bt-input-text mr5" name="d_mode" type="text" style="width:120px;" placeholder="权限">\
						<button class="btn btn-success btn-sm va0 pull-right" onclick="system_reinforcement.add_safe_config(\''+ s_key + '\');">添加</button>\</div>\
						<div class="divtable">\
						<div id="jc-file-table" class="table_head_fix" style="max-height:300px;overflow:auto;border:#ddd 1px solid">\
						<table class="table table-hover" style="border:none">\
							<thead>\
								<tr>\
									<th width="360">路径</th>\
									<th>模式</th>\
									<th>权限</th>\
									<th>状态</th>\
									<th style="text-align: right;">操作</th>\
								</tr>\
							</thead>\
							<tbody class="gztr">'+ tbody+'</tbody>\
						</table>\
						</div>\
					</div>\
					<ul class="help-info-text c7 ptb10" style="margin-top: 5px;">\
						<li>【只读】无法修改、创建、删除文件和目录</li>\
						<li>【追加】只能追加内容，不能删除或修改原有内容</li>\
						<li>【权限】设置文件或目录在受保护状态下的权限(非继承),关闭保护后权限自动还原</li>\
						<li>【如何填写权限】请填写Linux权限代号,如:644、755、600、555等,如果不填写,则使用文件原来的权限</li>\
					</ul>\
				</div>',
				success:function (){

				}
			})
		},'获取系统加固配置');
	},

	/**
	 * @description 防护配置
	 */
	reinforceSystem:function (){
		var _that = this;
		return bt_tools.table({
			el: '#reinforceSystem',
			url: '/plugin?name=syssafe&action=a&s=get_safe_status',
			load: lan.security.system.protection_req,
			default: lan.security.system.protection_default, // 数据为空时的默认提示
			autoHeight: true,
			dataFilter: function (data) {
				$('#isReinforcement').prop('checked', data.open);
				return { data: data.list };
			},
			column: [
				{title: lan.security.system.name, fid:'name'},
				{title: lan.security.system.desc, fid:'ps'},
				{
					title: lan.security.system.status,
					fid:'open',
					type: 'switch',
					event: function (row, index, ev, key, that) {
						bt_tools.send({
							url:'/plugin?action=a&name=syssafe&s=set_safe_status',
							data:{ s_key: row.key }
						},function (rdata){
							bt_tools.msg(rdata);
							that.$refresh_table_list();
						}, function (rdata) {
							bt_tools.msg(rdata);
							$(ev.currentTarget).prop('checked', row[3]);
						}, lan.security.system.change_status_req);
					}
				},
				{
					title: lan.public.operate,
					type: 'group',
					width: 150,
					align: 'right',
					group: [{
						title: lan.public.set,
						event: function (row, index) {
							switch (row.key) {
								case 'ssh':
									_that.renderReinforceSSHView(row);
									break;
								case 'process':
									_that.renderReinforceAbnormalProcess(row);
									break;
								default:
									_that.renderReinforceSystemView(row);
									break;
							}
						}
					}]
				}
			]
		})
	},

	/**
	 * @description 渲染防护配置 服务加固、环境变量加固、用户加固、关键目录加固、计划任务加固
	 */
	renderReinforceSystemView:function (row){
		var that = this;
		bt_tools.open({
			title: lan.security.system.config + " [" + row.name + "]",
			area: ['700px', '600px'],
			btn:false,
			content:'<div class="pd20">\
				<div id="ReinforceSystemTable"></div>\
				<ul class="help-info-text c7 ptb10" style="margin-top: 5px;font-size: 12px;">\
					<li>' + lan.security.system.config_tips1 + '</li>\
					<li>' + lan.security.system.config_tips2 + '</li>\
					<li>' + lan.security.system.config_tips3 + '</li>\
					<li>' + lan.security.system.config_tips4 + '</li>\
				</ul>\
			</div>',
			success:function (){
				that.reinforceSystemFind(row.key);
			}
		})
	},


	/**
	 * @description 渲染指定系统加固配置列表信息
	 * @param {String} s_key 系统加固配置key
	 */
	reinforceSystemFind: function (s_key) {
		var _that = this;
		var chattrs = { "a": lan.security.system.append, "i": lan.security.system.read }
		return bt_tools.table({
			el: '#ReinforceSystemTable',
			url: '/plugin?name=syssafe&action=a&s=get_safe_config',
			default: lan.security.system.config_defualt, // 数据为空时的默认提示
			height: 350,
			beforeRequest: function (data) {
				return $.extend(data, { s_key: s_key });
			},
			dataFilter: function (data) {
				return { data: data.paths };
			},
			column: [
				{title: lan.security.system.path, fid:'path'},
				{title: lan.security.system.model, fid:'chattr', template: function (row) {
						return '<span>'+ chattrs[row.chattr] +'</span>';
					}},
				{title: lan.security.system.permissions, fid:'ps', template: function (row) {
						return '<span>'+ (row.s_mode === row.d_mode?row.s_mode:(row.s_mode + ' >> ' + row.d_mode)) +'</span>';
					}},
				{title: lan.security.system.status, fid:'state', template: function (row) {
						return '<span class="'+ (row.state?'bt_success':'bt_danger') +'">'+ (row.state?lan.security.system.protected:lan.security.system.unprotected) +'</span>';
					}},
				{
					title: lan.public.operate,
					type: 'group',
					width: 150,
					align: 'right',
					group: [{
						title: lan.public.del,
						event: function (row, index, ev, id, that) {
							bt_tools.send({
								url: '/plugin?name=syssafe&action=a&s=remove_safe_path',
								data: { s_key: s_key, path: row.path }
							}, function (rdata) {
								bt_tools.msg(rdata);
								that.$refresh_table_list();
							}, lan.security.system.del_config_req);
						}
					}]
				}
			],
			tootls:[{ // 按钮组
				type: 'group',
				list: [{
					title: lan.security.system.add_config_btn,
					active: true,
					event: function (ev, that) {
						_that.reinforceAddProtectFile(s_key, that);
					}
				}]
			}]
		})
	},

	/**
	 * @description 渲染添加保护文件/目录
	 * @param {String} s_key 系统加固配置key
	 */
	reinforceAddProtectFile: function (s_key, table) {
		bt_tools.open({
			title: lan.security.system.add_config_btn,
			area: '480px',
			btn: [lan.public.confirm, lan.public.cancel],
			skin:'addProtectFile',
			content: {
				class: 'pd20',
				form: [
					{
						label: lan.security.system.path,
						group:{
							type: 'text',
							name: 'path',
							width: '250px',
							icon: { type: 'glyphicon-folder-open', event: function (ev) { }, select: 'dir' },
							placeholder: lan.security.system.path_input,
						}
					},
					{
						label: lan.security.system.model,
						group:{
							type: 'select',
							name: 'chattr',
							width: '250px',
							list: [
								{ title: lan.security.system.read, value: 'i' },
								{ title: lan.security.system.append, value: 'a' },
							]
						}
					},
					{
						label: lan.security.system.permissions,
						group: {
							type: 'text',
							name: 'd_mode',
							width: '250px',
							placeholder: lan.security.system.permissions_input,
						}
					}
				]
			},
			yes: function (form, indexs) {
				if (form.path === '') return layer.msg(lan.security.system.path_val1, { icon: 2 });
				if (form.chattr === '') return layer.msg(lan.security.system.model_val1, { icon: 2 });
				if (form.d_mode === '') return layer.msg(lan.security.system.permissions_input, { icon: 2 });
				form.s_key = s_key;
				bt_tools.send({
					url: '/plugin?name=syssafe&action=a&s=add_safe_path',
					data: form
				}, function (rdata) {
					bt_tools.msg(rdata);
					layer.close(indexs);
					table.$refresh_table_list();
				}, lan.security.system.add_config_req);
			}
		})
	},

	/**
	 * @description 渲染配置SSH加固策略
	 * @param {object} row 表格单行数据
	 */
	renderReinforceSSHView: function (row) {
		bt_tools.open({
			title: lan.security.system.config + ' [' + row.name + ']',
			area: ['700px'],
			btn:false,
			content:'<div class="pd15">\
				<div style="border-bottom:#ccc 1px solid;padding-bottom:15px">\
					' + lan.security.system.ssh_view1 + '\
					<input class="bt-input-text" min="30" max="1800" name="s_cycle" type="number" value="0" style="width:80px;margin-right:8px;">' + lan.security.system.ssh_view2 + '\
					<input min="3" max="100" class="bt-input-text" name="s_limit_count" type="number" value="0" style="width:80px;margin-right:8px;">' + lan.security.system.ssh_view3 + '\
					<input min="60" class="bt-input-text" name="s_limit" type="number" value="0" style="width:80px;margin-right:8px;">' + lan.security.system.ssh_view4 + '\
					<button class="btn btn-success btn-sm va0 pull-right" id="saveSshConfig">' + lan.public.save + '</button>\
				</div>\
				<ul class="help-info-text c7 ptb10" style="margin-top: 5px;">\
					<li>' + lan.security.system.config_tips5 + '</li>\
					<li>' + lan.security.system.config_tips6 + '</li>\
					<li>' + lan.security.system.config_tips7 + '</li>\
				</ul>\
			</div>',
			success: function () {
				bt_tools.send({
					url: '/plugin?name=syssafe&action=a&s=get_ssh_config',
				}, function (rdata) {
					$('input[name="s_cycle"]').val(rdata.cycle);
					$('input[name="s_limit"]').val(rdata.limit);
					$('input[name="s_limit_count"]').val(rdata.limit_count);
				});

				// 保存配置
				$('#saveSshConfig').click(function () {
					var data = {
						cycle: $("input[name='s_cycle']").val(),
						limit: $("input[name='s_limit']").val(),
						limit_count: $("input[name='s_limit_count']").val()
					}
					if (data.cycle === '') return layer.msg(lan.security.system.ssh_view5, { icon: 2 });
					if (data.limit === '') return layer.msg(lan.security.system.ssh_view6, { icon: 2 });
					if (data.limit_count === '') return layer.msg(lan.security.system.ssh_view7, { icon: 2 });

					bt_tools.send({
						url: '/plugin?name=syssafe&action=a&s=save_ssh_config',
						data: data
					}, function (rdata) {
						bt_tools.msg(rdata);
					}, lan.security.system.ssh_view8);
				})
			}
		})
	},

	/**
	 * @description 渲染异常进程监控配置
	 * @param {object} row 表格单行数据
	 */
	renderReinforceAbnormalProcess: function (row) {
		var that = this;
		bt_tools.open({
			title: lan.security.system.config + ' [' + row.name + ']',
			area: ['700px', '600px'],
			btn:false,
			content:'<div class="pd20">\
				<div id="AbnormalProcessTable"></div>\
				<ul class="help-info-text c7 ptb10" style="margin-top: 5px;font-size: 12px;">\
					<li>' + lan.security.system.config_tips8 + '</li>\
					<li>' + lan.security.system.config_tips9 + '</li>\
				</ul>\
			</div>',
			success: function () {
				bt_tools.table({
					el: '#AbnormalProcessTable',
					url: '/plugin?name=syssafe&action=a&s=get_process_white',
					height: 343,
					dataFilter: function (rdata) {
						var data = []
						$.each(rdata, function (index, item) {
							data.push({ name: item })
						})
						return { data: data }
					},
					column: [
						{
							title: lan.security.system.process_name,
							fid: 'name'
						},
						{
							title: lan.public.operate,
							type: 'group',
							width: 150,
							align: 'right',
							group: [{
								title: lan.public.del,
								event: function (row, index, ev, id, that) {
									bt_tools.send({
										url: '/plugin?name=syssafe&action=a&s=remove_process_white',
										data: { process_name: row.name }
									}, function (rdata) {
										bt_tools.msg(rdata);
										that.$refresh_table_list();
									}, lan.security.system.del_process_req);
								}
							}]
						}
					],
					tootls:[{ // 按钮组
						type: 'group',
						list: [{
							title: lan.security.system.add_process_btn,
							active: true,
							event: function (ev, that) {
								bt_tools.open({
									title: lan.security.system.add_process_btn,
									area: '450px',
									btn: [lan.public.save, lan.public.cancel],
									skin:'addProtectFile',
									content: {
										class: 'pd20',
										form: [
											{
												label: lan.security.system.process_name,
												group:{
													type: 'text',
													name: 'process_name',
													width: '250px',
													placeholder: lan.security.system.process_name_input,
												}
											}
										]
									},
									yes: function (form, indexs) {
										if (form.process_name === '') return layer.msg(lan.security.system.process_name_input, { icon: 2 });
										bt_tools.send({
											url: '/plugin?name=syssafe&action=a&s=add_process_white',
											data: form
										}, function (rdata) {
											bt_tools.msg(rdata);
											layer.close(indexs);
											that.$refresh_table_list();
										}, lan.security.system.add_config_req)
									}
								})
							}
						}]
					}]
				})
			}
		})
	},

	/**
	 * @description 封锁IP
	 */
	reinforceBlockIp: function () {
		var _that = this;
		var table = bt_tools.table({
			el: '#reinforceBlockIp',
			url: '/plugin?name=syssafe&action=a&s=get_ssh_limit_info',
			default: lan.security.system.ip_list_default, // 数据为空时的默认提示
			autoHeight: true,
			dataFilter: function (data) {
				return {data:data};
			},
			column: [
				{title: lan.security.system.ip, fid: 'address'},
				{title: lan.security.system.unblock_time, fid:'end', width: 300, template:function (row){
						return '<span>'+ (row.end ? bt.format_data(row.end) : lan.security.system.manually_unblock) + '</span>';
					}},
				{
					title: lan.public.operate,
					type: 'group',
					width: 150,
					align: 'right',
					group: [{
						title: lan.security.system.unblock_now,
						event: function (row, index) {
							bt_tools.send({
								url: '/plugin?name=syssafe&action=a&s=remove_ssh_limit',
								data: { ip: row.address }
							}, function (rdata) {
								bt_tools.msg(rdata);
								_that.getBlockIp();
							}, lan.security.system.unblock_now_req);
						}
					}]
				}
			]
		});
		this.ipTable = table
		return table
	},

	/**
	 * @description 表格重新生成封锁IP
	 */
	getBlockIp: function () {
		if (this.ipTable) this.ipTable.$refresh_table_list()
	},

	/**
	 * @description 操作日志
	 */
	reinforceLog:function (){
		var _that = this;
		$('#reinforceLog').empty()
		return bt_tools.table({
			el: '#reinforceLog',
			url: '/data?action=getData',
			default: lan.security.system.operate_logs_default, // 数据为空时的默认提示
			autoHeight: true,
			beforeRequest: function (param) {
				return $.extend(param,{ search: 'System hardening', table:'logs', order:'id desc'});
			},
			tootls: [
				{ //分页显示
					type: 'page',
					numberStatus: true, //　是否支持分页数量选择,默认禁用
					jump: true, //是否支持跳转分页,默认禁用
				}
			],
			column: [
				{ title: lan.security.system.date, fid: 'addtime' },
				{ title: lan.security.system.detail, fid: 'log' },
			],
		})
	}
}

// 日志审计
var logAudit = {
	data:{},
	init: function () {
		this.getLogFiles();
		$('#logAudit .logAuditTab').empty();
		$('#logAudit').height($(window).height() - 180)
	},
	/**
	 * @description SSH管理列表
	 */
	event:function (){
		var that = this;
		
		$(window).unbind('resize').on('resize', function () {
			if ($('.logAuditTabContent').is(':hidden')) return;
			var height = $(window).height() - 180;
			$('#logAudit').height(height);
			$('#logAuditTable .divtable').css('max-height', height - 150);
		});

		$('.logAuditTab').unbind('click').on('click', '.logAuditItem',function (){
			var data = $(this).data(), list = [];
			$.each(data.list, function (key, val){
				list.push(val.log_file)
			});
			$(this).addClass('active').siblings().removeClass('active');
			that.getSysLogs({log_name: data.log_file, list: list, p:1});
		});

		$('#logAuditPages').unbind('click').on('click', 'a', function (){
			var page = $(this).data('page');
			that.getSysLogs({log_name: that.data.log_name, list: that.data.list, p: page});
			return false;
		});
	},

	/**
	 * @description 获取日志审计类型
	 */
	getLogFiles: function () {
		var that = this;
		bt_tools.send({
			url: '/safe/syslog/get_sys_logfiles'
		}, function (rdata) {
			if(rdata.hasOwnProperty('status') ){
				if(!rdata.status && rdata.msg === 'Sorry, this feature is only available for Pro users!') {
					$('.logAuditTabContent').hide();
					$('#logAudit .daily-thumbnail').show();
					$('#logAudit').css('height', 'auto');
					return false;
				}
			}
			var initData = rdata[0], list = []
			$.each(rdata, function (i, v) {
				var logSize = 0;
				$.each(v.list,function (key, val){
					logSize += val.size;
				})
				$('#logAudit .logAuditTab').append($('<div class="logAuditItem" title="'+ (v.name + ' - '+ v.title +'('+ ToSize(v.size)) +'" data-file="'+ v.log_file +'">' + v.name + ' - '+ v.title +'('+ ToSize(v.size + logSize) +')</div>').data(v))
			})
			$('#logAudit .logAuditTab .logAuditItem:eq(0)').trigger('click')
		}, { load: lan.security.logs.get_logfiles, verify: false })
	},

	/**
	 * @description 获取日志审计类型列表
	 */
	getSysLogs: function (param) {
		var that = this;
		var page = param.p || 1;
		that.data = { log_name: param.log_name, list: param.list, limit: 20, p: page }
		bt_tools.send({
			url: '/safe/syslog/get_sys_log',
			data: {data:JSON.stringify(that.data)}
		}, function (rdata) {
			if(typeof rdata[0] === 'string'){
				$('#logAuditPre').show().siblings().hide()
				that.renderLogsAuditCommand(rdata)
			}else{
				$('#logAuditTable,#logAuditPages').show()
				$('#logAuditPre').hide()
				that.renderLogsAuditTable({ p:page }, rdata)
			}
		}, {
			load: lan.security.logs.get_sys_logs,
			verify: false
		})
	},

	/**
	 * @description 渲染日志审计命令
	 * @param {Object} rdata 参数
	 */
	renderLogsAuditCommand: function (rdata) {
		var logAuditLogs = $('#logAuditPre');
		var str = rdata.join('\r').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
		logAuditLogs.html('<pre style="height: 600px; background-color: #333; color: #fff; overflow-x: hidden; word-wrap:break-word; white-space:pre-wrap;">' + str + '</pre>');
		logAuditLogs.find('pre').scrollTop(9999999999999).css({height: $(window).height() - 180})
	},

	/**
	 * @description 渲染日志审计表格
	 * @param {object} param 参数
	 */
	renderLogsAuditTable: function (param, rdata){
		var that = this;
		var column = [], data = rdata[0] ? rdata[0] : { 'Time': '--', 'Role': '--', 'Event': '--' }, i = 0;
		$.each(data, function (key) {
			// console.log(key === '时间',i)
			column.push({ title: key, fid: key,width: (key === 'Time' &&  i === 0) ? '200px' : (key === 'Time'?'300px':'') })
			i++;
		})
		$('#logAuditTable').empty()
		return bt_tools.table({
			el: '#logAuditTable',
			url:'/safe/syslog/get_sys_log',
			default: lan.security.logs.logs_default, // 数据为空时的默认提示
			column: column,
			dataFilter: function (data) {
				if(typeof data.status === "boolean" && !data.status){
					$('.logAuditTabContent').hide().next().show();
					return { data: [] }
				}
				if(typeof data[0] === 'string'){
					$('#logAuditPre').show().siblings().hide()
					that.renderLogsAuditCommand(rdata)
				}else{
					$('#logAuditTable,#logAuditPages').show()
					$('#logAuditPre').hide()
					return {data:data}
				}
			},
			beforeRequest: function (param) {
				delete  param.data
				return {data:JSON.stringify($.extend(that.data,param))}
			},
			tootls: [{ // 按钮组
				type: 'group',
				list: [{
					title: lan.security.logs.refresh,
					active: true,
					event: function (ev) {
						that.getSysLogs(that.data)
					}
				}]
			},{ // 搜索内容
				type: 'search',
				width: '300px',
				placeholder: lan.security.logs.search,
				searchParam: 'search', //搜索请求字段，默认为 search
			},{
				type:'page',
				number:20
			}],
			success:function (config){
				$('#logAuditTable .divtable').css('max-height', $(window).height()  - 280)
			}
		})
	}
}

// 面板日志
var logs = {
	init: function () {
		$('#logsBody .tab-nav-border span').eq(0).trigger('click');
	},
	/**
	 * @description 事件绑定
	 */
	event:function (){
		var that = this;
		$('#logsBody').unbind('click').on('click','.tab-nav-border span',function(){
			var index = $(this).index();
			that.cutLogsTab(index);
		});
		$(window).unbind('resize').resize(function (){
			$('#runningLog .crontab-log').height((window.innerHeight - 310) +'px')
		});
	},

	/**
	 * @description 切换日志菜单
	 * @param {number} index 索引
	 */
	cutLogsTab:function(index){
		switch (index) {
			case 0:
				this.operationLogTable()
				break;
			case 1:
				this.runningLog()
				break;
		}
	},

	/**
	 * @description 日志表格
	 */
	operationLogTable:function(){
		var that = this;
		return bt_tools.table({
			el: '#operationLog',
			url: '/data?action=getData',
			default:  lan.security.logs.operate_default, // 数据为空时的默认提示
			autoHeight: true,
			beforeRequest: function (data) {
				return $.extend(data, {table: 'logs',order: 'id desc'})
			},
			tootls: [
				{ // 按钮组
					type: 'group',
					list: [{
						title: lan.security.logs.refresh,
						active:true,
						event: function (ev, _that) {
							_that.$refresh_table_list(true)
						}
					},{
						title: lan.security.logs.clear,
						event: function (ev) {
							bt.firewall.clear_logs(function(){
								that.operationLogTable()
							});
						}
					}]
				},
				{ // 搜索内容
					type: 'search',
					placeholder: lan.security.logs.operate_search,
					searchParam: 'search', //搜索请求字段，默认为 search
				},
				{ //分页显示
					type: 'page',
					numberStatus: true, //　是否支持分页数量选择,默认禁用
					jump: true, //是否支持跳转分页,默认禁用
				}],
			column: [
				{title: lan.security.logs.user, fid: 'username', width: 80},
				{title: lan.security.logs.type, fid: 'type', width: 150},
				{title: lan.security.logs.details,fid: 'log'},
				{title: lan.security.logs.time, fid: 'addtime', width:150}
			]
		})
	},

	/**
	 * @description 运行日志
	 */
	runningLog:function (){
		var that = this;
		bt_tools.send({
			url:'/config?action=get_panel_error_logs'
		},function (rdata){
			$('#runningLog').html('<div style="font-size: 0;">\
				<button type="button" title="' + lan.security.logs.refresh + '" class="btn btn-success btn-sm mr5 refreshRunLogs" ><span>' + lan.security.logs.refresh + '</span></button>\
				<button type="button" title="' + lan.security.logs.clear + '" class="btn btn-default btn-sm mr5 clearRunningLog" ><span>' + lan.security.logs.clear + '</span></button>\
				<pre class="crontab-log">'+ (rdata.msg || lan.security.logs.no_logs) +'</pre>\
			</div>');
			$('.refreshRunLogs').click(function (){
				that.runningLog();
			})
			$('.clearRunningLog').click(function (){
				that.clearRunningLog();
			})

			$('#runningLog .crontab-log').height((window.innerHeight - 310) +'px')
			var div = document.getElementsByClassName('crontab-log')[0]
			div.scrollTop = div.scrollHeight;
		}, lan.security.logs.get_logs_req);
	},

	/**
	 * @description 清除日志
	 */
	clearRunningLog:function (){
		var that = this;
		bt.confirm({
			title: lan.security.logs.clear_logs_title,
			msg: lan.security.logs.clear_logs_msg,
		},function (){
			bt_tools.send({
				url:'/config?action=clean_panel_error_logs'
			},function (rdata){
				bt.msg(rdata)
				that.runningLog()
			}, lan.security.logs.clear_logs_req)
		})
	}
}

firewall.init();
