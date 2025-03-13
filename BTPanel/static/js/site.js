$('#cutMode .tabs-item').on('click', function () {
	var type = $(this).data('type');
	var index = $(this).index();
	$(this).addClass('active').siblings().removeClass('active');
	$('#site_table_view').find('.tab-con-block').eq(index).removeClass('hide').siblings().addClass('hide');
	switch (type) {
		case 'php':
			$('#bt_site_table').empty();
			if (!isSetup) {
				$('.site_table_view .mask_layer')
					.removeClass('hide')
					.find('.prompt_description')
					.html(
						'Web server is not installed,<a href="javascript:;" class="btlink" onclick="bt.soft.install(\'nginx\')">Install Nginx</a>&nbsp;&nbsp;|&nbsp;&nbsp;<a href="javascript:;" class="btlink" onclick="bt.soft.install(\'apache\')">Install Apache</a>'
					);
			} else {
				$('.site_table_view .mask_layer').addClass('hide');
			}
			product_recommend.init(function () {
				site.php_table_view();
			});
			// site.get_types();
			break;
		case 'nodejs':
			$('#bt_node_table').empty();
			$.get('/plugin?action=getConfigHtml', { name: 'nodejs' }, function (res) {
				// if(typeof res !== 'string') $('.site_table_view .mask_layer').removeClass('hide').find('.prompt_description').html('Node version manager is not installed，<a href="javascript:;" class="btlink" onclick="bt.soft.install(\'nodejs\')">Click install</a>');
				if (typeof res !== 'string') {
					$('#bt_node_table+.mask_layer')
						.removeClass('hide')
						.find('.prompt_description')
						.html('Node version manager is not installed，<a href="javascript:;" class="btlink" onclick="bt.soft.install(\'nodejs\')">Click install</a>');
				} else {
					$('#bt_node_table+.mask_layer').addClass('hide');
				}
			});
			site.node_porject_view();
			break;
	}
	bt.set_cookie('site_model', type);
});

var site_table;
var node_table;
var countryList = [];
var site = {
	node: {
		/**
		 * @description 选择路径配置
		 * @return config {object} 选中文件配置
		 *
		 */
		get_project_select_path: function (path) {
			var that = this;
			return {
				type: 'text',
				width: '320px',
				name: 'project_script',
				value: path,
				placeholder: 'Please select the project startup file and enter the startup command. It cannot be empty',
				icon: {
					type: 'glyphicon-folder-open',
					select: 'file',
					event: function (ev) {},
				},
			};
		},
		get_project_select: function (path) {
			var that = this;
			return {
				type: 'select',
				name: 'project_script',
				width: '200px',
				disabled: true,
				unit: '* Get the startup mode in package.json',
				placeholder: 'Select the project continue',
				list: path
					? function (configs) {
							that.get_project_script_list(path, configs[2], this);
					  }
					: [],
				change: function (formData, elements, formConfig) {
					var project_script = $("[data-name='project_script']");
					if (formData.project_script === '') {
						if ($('#project_script_two').length === 0) {
							project_script
								.parent()
								.after(
									'<div class="inlineBlock"><input type="text" name="project_script_two" id="project_script_two" placeholder="Please select the startup file and startup command, it cannot be empty" class="mt5 bt-input-text mr10 " style="width:420px;" value="" /><span class="glyphicon glyphicon-folder-open cursor" onclick="bt.select_path(\'project_script_two\',\'all\',null,\'' +
										path +
										'\')" style="margin-right: 18px;"></span></div>'
								);
						}
					} else {
						project_script.parent().next().remove();
					}
				},
			};
		},

		/**
		 * @description 选择启动脚本配置
		 * @param path {string} 项目目录
		 * @param form {object} 表单元素
		 * @param formObject {object} 表单对象
		 * @return config {object} 选中文件配置
		 */
		get_project_script_list: function (path, form, formObject) {
			var that = this;
			that.get_start_command(
				{ project_cwd: path },
				function (res) {
					var arry = [];
					for (var resKey in res) {
						arry.push({ title: resKey + ' 【' + res[resKey] + '】', value: resKey });
					}
					arry.push({ title: 'Custom command', value: '' });
					form.group = that.get_project_select(path);
					form.group.list = arry;
					form.group.disabled = false;
					formObject.$replace_render_content(2);
					if (arry.length === 1) {
						var project_script = $("[data-name='project_script']");
						// form.group.value = '';
						project_script
							.parent()
							.after(
								'<div class="inlineBlock"><input type="text" name="project_script_two" id="project_script_two" placeholder="Please select the startup file and startup command, it cannot be empty" class="mt5 bt-input-text mr10 " style="width:420px;" value="" /><span class="glyphicon glyphicon-folder-open cursor" onclick="bt.select_path(\'project_script_two\',\'file\',null,\'' +
									path +
									'\')" style="margin-right: 18px;"></span></div>'
							);
					}
				},
				function () {
					form.label = 'Start file/command';
					form.group = that.get_project_select_path(path);
					formObject.$replace_render_content(2);
				}
			);
			return [];
		},

		/**
		 *
		 * @description 获取Node版本列表
		 * @return {{dataFilter: (function(*): *[]), url: string}}
		 */
		get_node_version_list: function () {
			return {
				url: '/project/nodejs/get_nodejs_version',
				dataFilter: function (res) {
					if (res.length === 0) {
						layer.closeAll();
						bt.msg({
							status: false,
							msg: 'Please open [Node Version Manager], install at least 1 Node version to continue',
						});
						return;
					}
					var arry = [];
					for (var i = 0; i < res.length; i++) {
						arry.push({ title: res[i], value: res[i] });
					}
					return arry;
				},
			};
		},

		/**
		 * @description 获取Node通用Form配置
		 * @param config {object} 获取配置参数
		 * @return form模板
		 */
		get_node_general_config: function (config) {
			config = config || {};
			var that = this,
				formLineConfig = [
					{
						label: 'Path',
						group: {
							type: 'text',
							width: '350px',
							name: 'project_cwd',
							readonly: true,
							icon: {
								type: 'glyphicon-folder-open',
								event: function (ev) {},
								callback: function (path) {
									var filename = path.split('/');
									var project_script_config = this.config.form[2],
										project_name_config = this.config.form[1],
										project_ps_config = this.config.form[6];
									project_name_config.group.value = filename[filename.length - 1];
									project_ps_config.group.value = filename[filename.length - 1];
									project_script_config.group.disabled = false;
									this.$replace_render_content(1);
									this.$replace_render_content(6);
									that.get_project_script_list(path, project_script_config, this);
								},
							},
							value: bt.get_cookie('sites_path') ? bt.get_cookie('sites_path') : '/www/wwwroot',
							placeholder: 'Please select the project directory',
						},
					},
					{
						label: 'Name',
						group: {
							type: 'text',
							name: 'project_name',
							width: '350px',
							placeholder: 'Please enter the name of the Node project',
							input: function (formData, formElement, formConfig) {
								var project_ps_config = formConfig.config.form[6];
								project_ps_config.group.value = formData.project_name;
								formConfig.$replace_render_content(6);
							},
						},
					},
					{
						label: 'Run opt',
						group: (function () {
							return that.get_project_select(config.path);
						})(),
					},
					{
						label: 'Port',
						group: {
							type: 'number',
							name: 'port',
							width: '200px',
							placeholder: 'Port of the project',
							unit: '* Port of the project',
						},
					},
					{
						label: 'User',
						group: {
							type: 'select',
							name: 'run_user',
							width: '150px',
							unit: '* No special requirements,choose www user',
							list: [
								{ title: 'www', value: 'www' },
								{ title: 'root', value: 'root' },
							],
							tips: 'sssss',
						},
					},
					{
						label: 'Node',
						group: {
							type: 'select',
							name: 'nodejs_version',
							width: '150px',
							unit: '* Choose the right Node version, <a href="javascript:;" class="btlink" onclick="bt.soft.set_lib_config(\'nodejs\',\'Node.js version manager\')">Install other</a>',
							list: (function () {
								return that.get_node_version_list();
							})(),
						},
					},
					{
						label: 'Remarks',
						group: {
							type: 'text',
							name: 'project_ps',
							width: '420px',
							placeholder: 'Please enter project remarks',
							value: config.ps,
						},
					},
					{
						label: 'Domain name',
						group: {
							type: 'textarea', //当前表单的类型 支持所有常规表单元素、和复合型的组合表单元素
							name: 'domains', //当前表单的name
							style: { width: '420px', height: '120px', 'line-height': '22px' },
							tips: {
								//使用hover的方式显示提示
								text: '<span>Please enter the domain name to be bound, this option can be empty</span><br>One domain name per line, the default is port 80<br>Pan-analysis adding method *.domain.com<br>If the format of the additional port is www.domain.com:88',
								style: { top: '10px', left: '15px' },
							},
						},
					},
					{
						group: {
							type: 'help',
							list: [
								'[Run opt]: The scripts list in package.json is read by default, or you can select the [Custom Command] option to manually enter the start command',
								'[Custom start]: You can select the startup file or directly enter the startup command. Supported startup methods: npm/node/pm2/yarn',
								'[Port]：The wrong port will lead to access to 502, if you dont know the port, you can change to the correct port after starting',
								'[User]：For security reasons, the www user is used by default to run, and root user running may bring security risks',
							],
						},
					},
				];

			if (config.path) {
				formLineConfig.splice(-1, 1);
				return formLineConfig.concat([
					{
						label: 'Boot',
						group: {
							type: 'checkbox',
							name: 'is_power_on',
							width: '220px',
							title: 'Follow the system to start the service',
						},
					},
					{
						label: '',
						group: {
							type: 'button',
							name: 'saveNodeConfig',
							title: 'Save',
							event: function (data, form, that) {
								if (data.project_cwd === '') {
									bt.msg({ status: false, msg: 'The project directory cannot be empty' });
									return false;
								}
								var project_script_two = $('[name="project_script_two"]');
								if ((data.project_script === '' && project_script_two.length < 1) || (project_script_two.length > 1 && project_script_two.val() === '')) {
									bt.msg({ status: false, msg: 'Start file/command cannot be empty' });
									return false;
								}
								if (data.port === '') {
									bt.msg({ status: false, msg: 'Project port cannot be empty' });
									return false;
								}
								if (data.project_script === '') {
									data.project_script = project_script_two.val();
									delete data.project_script_two;
								}
								config.callback(data, form, that);
							},
						},
					},
				]);
			}
			return formLineConfig;
		},

		/**
		 * @description 添加node项目表单
		 * @returns {{form: 当前实例对象, close: function(): void}}
		 */
		add_node_form: function (callback) {
			var that = this;
			var add_node_project = bt_tools.open({
				title: 'Add Node project',
				area: '700px',
				btn: ['Confirm', 'Cancel'],
				content: {
					class: 'pd30',
					form: (function () {
						return that.get_node_general_config({
							form: add_node_project,
						});
					})(),
				},
				yes: function (form, indexs, layers) {
					var defaultParam = {
						bind_extranet: 0,
						is_power_on: 1,
						max_memory_limit: 4096,
						project_env: '',
					};
					if (form.domains !== '') {
						var arry = form.domains.replace('\n', '').split('\r'),
							newArry = [];
						for (var i = 0; i < arry.length; i++) {
							var item = arry[i];
							if (bt.check_domain(item)) {
								newArry.push(item.indexOf(':') > -1 ? item : item + ':80');
							} else {
								bt.msg({
									status: false,
									msg: '[' + item + '] The format of the bound domain name is incorrect',
								});
								break;
							}
						}
						defaultParam.bind_extranet = 1;
						defaultParam.domains = newArry;
					}
					if (form.project_name === '') {
						bt.msg({ status: false, msg: 'Project name cannot be empty' });
						return false;
					}
					var project_script_two = $('[name="project_script_two"]');
					if (project_script_two.length && project_script_two.val() === '') {
						bt.msg({ status: false, msg: 'Please enter a custom startup command, it cannot be empty!' });
						return false;
					}
					if (form.port === '') {
						bt.msg({ status: false, msg: 'Project port cannot be empty' });
						return false;
					}
					if (form.project_script === null) {
						bt.msg({ status: false, msg: 'Please select the project directory to get the start command!' });
						return false;
					}
					form = $.extend(form, defaultParam);
					if (project_script_two.length) {
						form.project_script = project_script_two.val();
						delete form.project_script_two;
					}
					var _command = null;
					setTimeout(function () {
						if (_command < 0) return false;
						_command = that.request_module_log_command({ shell: 'tail -f /www/server/panel/logs/npm-exec.log' });
					}, 500);
					site.node.add_node_project(form, function (res) {
						if (!res.status) _command = -1;
						if (_command > 0) layer.close(_command);
						if (callback) callback(res, indexs);
					});
				},
			});
			return add_node_project;
		},

		/**
		 * @description 添加node项目请求
		 * @param param {object} 请求参数
		 * @param callback {function} 回调函数
		 */
		add_node_project: function (param, callback) {
			this.http({ create_project: false, verify: false }, param, callback);
		},

		/**
		 * @description 获取Node环境
		 * @param callback {function} 回调函数
		 */
		get_node_environment: function (callback) {
			bt_tools.send(
				{
					url: '/project/nodejs/is_install_nodejs',
				},
				function (res) {
					if (callback) callback(res);
				},
				{ load: 'Get the Node project environment' }
			);
		},

		/**
		 * @description 编辑Node项目请求
		 * @param param {object} 请求参数
		 * @param callback {function} 回调函数
		 */
		modify_node_project: function (param, callback) {
			this.http({ modify_project: 'Modify Node project configuration' }, param, callback);
		},

		/**
		 * @description 删除Node项目请求
		 * @param param {object} 请求参数
		 * @param callback {function} 回调函数
		 */
		remove_node_project: function (param, callback) {
			this.http({ remove_project: 'Delete Node project' }, param, callback);
		},

		/**
		 * @description 获取node项目域名
		 * @param callback {function} 回调行数
		 */
		get_node_project_domain: function (callback) {
			this.http({ project_get_domain: 'Get the list of Node project domain names' }, callback);
		},

		/**
		 * @description 获取启动命令列表
		 * @param param {object} 请求参数
		 * @param callback {function} 成功回调行数
		 * @param callback1 {function} 错误回调行数
		 */
		get_start_command: function (params, callback, callback1) {
			this.http({ get_run_list: 'Getting project start command' }, params, callback, callback1);
		},
		/**
		 * @description 添加Node项目域名
		 * @param param {object} 请求参数
		 * @param callback {function} 回调行数
		 */
		add_node_project_domain: function (param, callback) {
			this.http({ project_add_domain: false, verify: false }, param, callback);
		},

		/**
		 * @description 删除Node项目域名
		 * @param param {object} 请求参数
		 * @param callback {function} 回调行数
		 */
		remove_node_project_domain: function (param, callback) {
			this.http({ project_remove_domain: 'Delete the Node project domain name' }, param, callback);
		},

		/**
		 * @description 启动Node项目
		 * @param param {object} 请求参数
		 * @param callback {function} 回调行数
		 */
		start_node_project: function (param, callback) {
			this.http({ start_project: 'Enable Node project' }, param, callback);
		},

		/**
		 * @description 停止Node项目
		 * @param param {object} 请求参数
		 * @param callback {function} 回调行数
		 */
		stop_node_project: function (param, callback) {
			this.http({ stop_project: 'Stop the Node project' }, param, callback);
		},

		/**
		 * @description 重启Node项目
		 * @param param {object} 请求参数
		 * @param callback {function} 回调行数
		 */
		restart_node_project: function (param, callback) {
			this.http({ restart_project: 'Restart the Node project' }, param, callback);
		},

		/**
		 * @description 获取值指定Node项目信息
		 * @param param {object} 请求参数
		 * @param callback {function} 回调行数
		 */
		get_node_project_info: function (param, callback) {
			this.http({ get_project_info: 'Get Node project information' }, param, callback);
		},

		/**
		 * @description 绑定外网映射
		 * @param param {object} 请求参数
		 * @param callback {function} 回调行数
		 */
		bind_node_project_map: function (param, callback) {
			this.http({ bind_extranet: 'Mapping', verify: false }, param, callback);
		},
		/**
		 * @description 绑定外网映射
		 * @param param {object} 请求参数
		 * @param callback {function} 回调行数
		 */
		unbind_node_project_map: function (param, callback) {
			this.http({ unbind_extranet: 'Unmapping', verify: false }, param, callback);
		},
		/**
		 * @description 安装node项目依赖
		 * @param param {object} 请求参数
		 * @param callback {function} 回调行数
		 */
		install_node_project_packages: function (param, callback) {
			this.http({ install_packages: false, verify: false }, param, callback);
		},

		/**
		 * @description 安装指定模块
		 * @param param {object} 请求参数
		 * @param callback {function} 回调行数
		 */
		npm_install_node_module: function (param, callback) {
			this.http({ install_module: 'Install Node module' }, param, callback);
		},
		/**
		 * @description 更新指定模块
		 * @param param {object} 请求参数
		 * @param callback {function} 回调行数
		 */
		upgrade_node_module: function (param, callback) {
			this.http({ upgrade_module: 'Update Node module' }, param, callback);
		},
		/**
		 * @description 删除指定模块
		 * @param param {object} 请求参数
		 * @param callback {function} 回调行数
		 */ uninstall_node_module: function (param, callback) {
			this.http({ uninstall_module: 'Uninstall the Node module' }, param, callback);
		},
		/**
		 * @description 模拟点击
		 */
		simulated_click: function (num) {
			$('.bt-w-menu p:eq(' + num + ')').click();
		},
		/**
		 * @description 获取Node项目信息
		 * @param row {object} 当前行，项目信息
		 */
		set_node_project_view: function (row) {
			var that = this;
			bt.open({
				type: 1,
				title: 'Node project management-[' + row.name + '], add time [' + row.addtime + ']',
				skin: 'node_project_dialog',
				area: ['800px', '700px'],
				content:
					'<div class="bt-form">' +
					'<div class="bt-w-menu site-menu pull-left"></div>' +
					'<div id="webedit-con" class="bt-w-con pd15" style="height:100%; overflow-y: auto;">' +
					'</div>' +
					'<div class="mask_module hide"><div class="node_mask_module_text">Please turn on <a href="javascript:;" class="btlink mapExtranet" onclick="site.node.simulated_click(2)"> mapping </a>to viewing the configuration information</div></div>' +
					'</div>',
				btn: false,
				success: function (layers) {
					var $layers = $(layers),
						$content = $layers.find('#webedit-con');

					function reander_tab_list(config) {
						for (var i = 0; i < config.list.length; i++) {
							var item = config.list[i],
								tab = $('<p class="' + (i === 0 ? 'bgw' : '') + '">' + item.title + '</p>');
							$(config.el).append(tab);
							(function (i, item) {
								tab.on('click', function (ev) {
									$('.mask_module').addClass('hide');
									$(this).addClass('bgw').siblings().removeClass('bgw');
									if ($(this).hasClass('bgw')) {
										that.get_node_project_info({ project_name: row.name }, function (res) {
											config.list[i].event.call(that, $content, res, ev);
										});
									}
								});
								if (item.active) tab.click();
							})(i, item);
						}
					}

					reander_tab_list({
						el: $layers.find('.bt-w-menu'),
						list: [
							{
								title: 'Project config',
								active: true,
								event: that.reander_node_project_config,
							},
							{
								title: 'Domain',
								event: that.reander_node_domain_manage,
							},
							{
								title: 'Mapping',
								event: that.reander_node_project_map,
							},
							{
								title: 'URL rewrite',
								event: that.reander_node_project_rewrite,
							},
							{
								title: 'Config file',
								event: that.reander_node_file_config,
							},
							{
								title: 'SSL',
								event: that.reander_node_project_ssl,
							},
							{
								title: 'Load status',
								event: that.reander_node_service_condition,
							},
							{
								title: 'service status',
								event: that.reander_node_service_status,
							},
							{
								title: 'Module',
								event: that.reander_node_project_module,
							},
							{
								title: 'Project log',
								event: that.reander_node_project_log,
							},
							{
								title: 'Website log',
								event: that.reander_node_site_log,
							},
						],
					});
				},
			});
		},

		/**
		 * @description 渲染Node项目配置视图
		 * @param el {object} 当前element节点
		 * @param row {object} 当前项目数据
		 * @param that {object} 当前node项目对象
		 */
		reander_node_project_config: function (el, rows) {
			var row = $.extend(true, {}, rows);
			var that = this,
				edit_node_project = bt_tools.form({
					el: '#webedit-con',
					data: row.project_config,
					class: 'ptb10',
					form: (function () {
						var fromConfig = that.get_node_general_config({
							form: edit_node_project,
							path: row.path,
							ps: row.ps,
							callback: function (data, form, formNew) {
								data['is_power_on'] = data['is_power_on'] ? 1 : 0;
								var project_script_two = $('[name="project_script_two"]');
								if (project_script_two.length && project_script_two.val() === '') {
									bt.msg({
										status: false,
										msg: 'Please enter a custom startup command, it cannot be empty!',
									});
									return false;
								}
								if (form.port === '') {
									bt.msg({ status: false, msg: 'Project port cannot be empty' });
									return false;
								}
								if (form.project_script === null) {
									bt.msg({
										status: false,
										msg: 'Please select the project directory to get the start command!',
									});
									return false;
								}
								site.node.modify_node_project(data, function (res) {
									if (res.status) {
										row['project_config'] = $.extend(row, data);
										row['path'] = data.project_script;
										row['ps'] = data.ps;
									}
									bt.msg({ status: res.status, msg: res.data });
									site.node.simulated_click(0);
								});
							},
						});
						setTimeout(function () {
							var is_existence = false,
								list = fromConfig[2].group.list;
							for (var i = 0; i < list.length; i++) {
								var item = list[i];
								if (item.value === rows.project_config.project_script) {
									is_existence = true;
									break;
								}
							}
							if (!is_existence && list.length > 1) {
								$('[data-name="project_script"] li:eq(' + (list.length - 1) + ')').click();
								$('[name="project_script_two"]').val(rows.project_config.project_script);
							}
							if (list.length === 1) {
								$('[data-name="project_script"] li:eq(0)').click();
								$('[name="project_script_two"]').val(rows.project_config.project_script);
							}
						}, 250);

						fromConfig[1].group.disabled = true;
						fromConfig[fromConfig.length - 3].hide = true;
						fromConfig[fromConfig.length - 3].group.disabled = true;
						return fromConfig;
					})(),
				});
			setTimeout(function () {
				$(el).append(
					'<ul class="help-info-text c7">' +
						'<li>[Run opt]: The scripts list in package.json is read by default, or you can select the [Custom Command] option to manually enter the start command</li>' +
						'<li>[Custom command]: You can select the startup file or directly enter the startup command. Supported startup methods: npm/node/pm2/yarn</li>' +
						'<li>[Port]：The wrong port will lead to access to 502, if you don’t know the port, you can fill it out at will, and then change to the correct port after starting the project</li>' +
						'<li>[User]：For security reasons, the www user is used by default to run, and root user running may bring security risks</li>' +
						'</ul>'
				);
				if (!row.listen_ok)
					$(el)
						.find('input[name="port"]')
						.parent()
						.after(
							'<div class="block mt10" style="margin-left: 100px;color: red;line-height: 20px;">The project port may be wrong, it is detected that the current project listens to the following ports[ ' +
								row.listen.join('/') +
								' ]</div>'
						);
			}, 100);
		},

		/**
		 * @description 渲染Node项目服务状态
		 * @param el {object} 当前element节点
		 * @param row {object} 当前项目数据
		 */
		reander_node_service_status: function (el, row) {
			var arry = [
					{ title: 'Start', event: this.start_node_project },
					{ title: 'Stop', event: this.stop_node_project },
					{ title: 'Restart', event: this.restart_node_project },
				],
				that = this,
				html = $('<div class="soft-man-con bt-form"><p class="status"></p><div class="sfm-opt"></div></div>');

			function reander_service(status) {
				var status_info = status ? ['Start', '#20a53a', 'play'] : ['Stop', 'red', 'pause'];
				return 'Status: <span>' + status_info[0] + '</span><span style="color:' + status_info[1] + '; margin-left: 3px;" class="glyphicon glyphicon glyphicon-' + status_info[2] + '"></span>';
			}

			html.find('.status').html(reander_service(row.run));
			el.html(html);
			for (var i = 0; i < arry.length; i++) {
				var item = arry[i],
					btn = $('<button class="btn btn-default btn-sm"></button>');
				(function (btn, item, indexs) {
					!(row.run && indexs === 0) || btn.addClass('hide');
					!(!row.run && indexs === 1) || btn.addClass('hide');
					btn
						.on('click', function () {
							bt.confirm(
								{
									title: item.title + 'Project-[' + row.name + ']',
									msg: 'Are you sure you want the' + item.title + 'item,' + (row.run ? 'The project may be affected,' : '') + 'continue?',
								},
								function (index) {
									layer.close(index);
									item.event.call(that, { project_name: row.name }, function (res) {
										row.run = indexs === 0 ? true : indexs === 1 ? false : row.run;
										html.find('.status').html(reander_service(row.run));
										$('.sfm-opt button').eq(0).addClass('hide');
										$('.sfm-opt button').eq(1).addClass('hide');
										$('.sfm-opt button')
											.eq(row.run ? 1 : 0)
											.removeClass('hide');
										bt.msg({ status: res.status, msg: res.data || res.error_msg });
									});
								}
							);
						})
						.text(item.title);
				})(btn, item, i);
				el.find('.sfm-opt').append(btn);
			}
		},

		/**
		 * @description 渲染Node项目域名管理
		 * @param el {object} 当前element节点
		 * @param row {object} 当前项目数据
		 */
		reander_node_domain_manage: function (el, row) {
			var that = this,
				list = [
					{
						class: 'mb0',
						items: [
							{
								name: 'nodedomain',
								width: '340px',
								type: 'textarea',
								placeholder:
									'Please enter the domain name to be mapped, this option can be empty<br>One domain name per line, default port 80<br>How to add wildcard domain names *.domain.com<br>Specify the port used www.domain.com:88',
							},
							{
								name: 'btn_node_submit_domain',
								text: 'Add',
								type: 'button',
								callback: function (sdata) {
									var arrs = sdata.nodedomain.split('\n');
									var domins = [];
									for (var i = 0; i < arrs.length; i++) domins.push(arrs[i]);
									that.add_node_project_domain({ project_name: row.name, domains: domins }, function (res) {
										bt.msg({ status: res.status, msg: res.data || res.error_msg });
										if (res.status) {
											$('[name=nodedomain]').val('');
											$('.placeholder').css('display', 'block');
											project_domian.$refresh_table_list(true);
										}
									});
								},
							},
						],
					},
				];
			var _form_data = bt.render_form_line(list[0]),
				loadT = null,
				placeholder = null;
			el.html(_form_data.html + '<div id="project_domian_list"></div>');
			bt.render_clicks(_form_data.clicks);
			// domain样式
			$('.btn_node_submit_domain').addClass('pull-right').css('margin', '30px 35px 0 0');
			$('textarea[name=nodedomain]').css('height', '120px');
			placeholder = $('.placeholder');
			placeholder
				.click(function () {
					$(this).hide();
					$('.nodedomain').focus();
				})
				.css({
					width: '340px',
					heigth: '120px',
					left: '0px',
					top: '0px',
					'padding-top': '10px',
					'padding-left': '15px',
				});
			$('.nodedomain')
				.focus(function () {
					placeholder.hide();
					loadT = layer.tips(placeholder.html(), $(this), { tips: [1, '#20a53a'], time: 0, area: $(this).width() });
				})
				.blur(function () {
					if ($(this).val().length == 0) placeholder.show();
					layer.close(loadT);
				});
			var project_domian = bt_tools.table({
				el: '#project_domian_list',
				url: '/project/nodejs/project_get_domain',
				default: 'No domain name list yet',
				param: { project_name: row.name },
				height: 375,
				beforeRequest: function (params) {
					if (params.hasOwnProperty('data') && typeof params.data === 'string') return params;
					return { data: JSON.stringify(params) };
				},
				column: [
					{ type: 'checkbox', class: '', width: 20 },
					{
						fid: 'name',
						title: 'Domain Name',
						type: 'text',
						template: function (row) {
							return '<a href="http://' + row.name + ':' + row.port + '" target="_blank" class="btlink">' + row.name + '</a>';
						},
					},
					{
						fid: 'port',
						title: 'Port',
						type: 'text',
					},
					{
						title: 'OPT',
						type: 'group',
						width: '100px',
						align: 'right',
						group: [
							{
								title: 'Del',
								event: function (rowc, index, ev, key, rthat) {
									bt.confirm(
										{
											title: 'Delete domain [ ' + row.name + ' ]',
											msg: lan.site.domain_del_confirm,
										},
										function () {
											that.remove_node_project_domain(
												{
													project_name: row.name,
													domain: rowc.name + ':' + rowc.port,
												},
												function (res) {
													bt.msg({ status: res.status, msg: res.data || res.error_msg });
													rthat.$refresh_table_list(true);
												}
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
						// 批量操作
						type: 'batch',
						positon: ['left', 'bottom'],
						placeholder: 'Please select bulk operation',
						buttonValue: 'Batch operation',
						disabledSelectValue: 'Please select the site that needs batch operation!',
						selectList: [
							{
								title: 'Delete domain name',
								load: true,
								url: '/project/nodejs/project_remove_domain',
								param: function (crow) {
									return {
										data: JSON.stringify({
											project_name: row.name,
											domain: crow.name + ':' + crow.port,
										}),
									};
								},
								callback: function (that) {
									// 手动执行,data参数包含所有选中的站点
									bt.show_confirm('Delete domain names in bulk', "<span style='color:red'>Delete the selected domain name at the same time, do you want to continue?</span>", function () {
										var param = {};
										that.start_batch(param, function (list) {
											var html = '';
											for (var i = 0; i < list.length; i++) {
												var item = list[i];
												html +=
													'<tr><td>' +
													item.name +
													'</td><td><div style="float:right;"><span style="color:' +
													(item.request.status ? '#20a53a' : 'red') +
													'">' +
													(item.request.status ? 'Success' : 'Fail') +
													'</span></div></td></tr>';
											}
											project_domian.$batch_success_table({
												title: 'Batch deletion',
												th: 'Delete domain name',
												html: html,
											});
											project_domian.$refresh_table_list(true);
										});
									});
								},
							},
						],
					},
				],
			});
			setTimeout(function () {
				$(el).append(
					'<ul class="help-info-text c7">' +
						'<li>If yours is an HTTP project and needs to be mapped, please bind at least one domain name</li>' +
						'<li>It is recommended that all domain names use the default port 80</li>' +
						'</ul>'
				);
			}, 100);
		},

		/**
		 * @description 渲染Node项目映射
		 * @param el {object} 当前element节点
		 * @param row {object} 当前项目数据
		 */
		reander_node_project_map: function (el, row) {
			var that = this;
			el.html(
				'<div class="pd15"><div class="ss-text mr50" style="display: block;height: 35px;">' +
					'   <em title="Mapping">Mapping</em>' +
					'       <div class="ssh-item">' +
					'           <input class="btswitch btswitch-ios" id="node_project_map" type="checkbox">' +
					'           <label class="btswitch-btn" for="node_project_map" name="node_project_map"></label>' +
					'       </div>' +
					'</div><ul class="help-info-text c7"><li>If your project is an HTTP project and you need to access the Internet through 80443, please use the mapping</li><li>Before using the mapping, please add at least 1 domain name in [Domain Name Management]</li></ul></div>'
			);
			$('#node_project_map').attr('checked', row['project_config']['bind_extranet'] ? true : false);
			$('[name=node_project_map]').click(function () {
				var _check = $('#node_project_map').prop('checked'),
					param = { project_name: row.name };
				if (!_check) param['domains'] = row['project_config']['domains'];
				layer.confirm(
					(!_check ? 'Enable' : 'Disable') + ' mapping!,do you want to continue?',
					{
						btn: ['Confirm', 'Cancel'],
						title: 'Mapping',
						icon: 0,
						closeBtn: 2,
						cancel: function () {
							$('#node_project_map').attr('checked', _check);
						},
					},
					function () {
						that[_check ? 'unbind_node_project_map' : 'bind_node_project_map'](param, function (res) {
							if (!res.status) $('#node_project_map').attr('checked', _check);
							bt.msg({ status: res.status, msg: typeof res.data != 'string' ? res.error_msg : res.data });
							row['project_config']['bind_extranet'] = _check ? 0 : 1;
						});
					},
					function () {
						$('#node_project_map').attr('checked', _check);
					}
				);
			});
		},

		/**
		 * @description 渲染Node项目模块
		 * @param el {object} 当前element节点
		 * @param row {object} 当前项目数据
		 */
		reander_node_project_module: function (el, row) {
			var that = this;
			el.html(
				'<div class="">' +
					'<div class=""><input class="bt-input-text mr5" name="mname" type="text" value="" style="width:240px" placeholder="Module name" /><button class="btn btn-success btn-sm va0 install_node_module" >Install</button><button class="btn btn-success btn-sm va0 pull-right npm_install_node_config">One-key install</button></div>' +
					'<div id="node_module_list"></div>' +
					'</div>'
			);
			var node_project_module_table = bt_tools.table({
				el: '#node_module_list',
				url: '/project/nodejs/get_project_modules',
				default: 'The module is not installed, click one-click to install the project module, the default prompt when the data is empty',
				param: { project_name: row.name, project_cwd: row.path },
				height: '576px',
				load: 'Retrieving module list, please wait...',
				beforeRequest: function (params) {
					if (params.hasOwnProperty('data') && typeof params.data === 'string') return params;
					return { data: JSON.stringify(params) };
				},
				column: [
					{
						fid: 'name',
						title: 'Module',
						type: 'text',
					},
					{
						fid: 'version',
						title: 'Ver',
						type: 'text',
						width: '60px',
					},
					{
						fid: 'license',
						title: 'License',
						type: 'text',
						template: function (row) {
							if (typeof row.license === 'object') return '<span>' + row.license.type + '<span>';
							return '<span>' + row.license + '</span>';
						},
					},
					{
						fid: 'description',
						title: 'Description',
						width: 235,
						type: 'text',
						template: function (row) {
							return '<span>' + row.description + '<a href="javascript:;"></a></span>';
						},
					},
					{
						title: 'OPT',
						type: 'group',
						width: '125px',
						align: 'right',
						group: [
							{
								title: 'Update',
								event: function (rowc, index, ev, key, rthat) {
									bt.show_confirm('Update module', "<span style='color:red'>Updating the [" + rowc.name + '] module may affect the operation of the project, continue?</span>', function () {
										that.upgrade_node_module({ project_name: row.name, mod_name: rowc.name }, function (res) {
											bt.msg({ status: res.status, msg: res.data || res.error_msg });
											rthat.$refresh_table_list(true);
										});
									});
								},
							},
							{
								title: 'Uninstall',
								event: function (rowc, index, ev, key, rthat) {
									bt.show_confirm('Uninstall the module', "<span style='color:red'>Uninstalling the [" + rowc.name + '] module may affect the operation of the project, continue?</span>', function () {
										that.uninstall_node_module(
											{
												project_name: row.name,
												mod_name: rowc.name,
											},
											function (res) {
												bt.msg({ status: res.status, msg: res.data || res.error_msg });
												rthat.$refresh_table_list(true);
											}
										);
									});
								},
							},
						],
					},
				],
				success: function (config) {
					// 隐藏一键安装
					if (config.data.length > 0) $('.npm_install_node_config').addClass('hide');
				},
			});
			//安装模块
			$('.install_node_module').on('click', function () {
				var _mname = $('input[name=mname]').val();
				if (!_mname) return layer.msg('Please enter the module name and version', { icon: 2 });
				that.npm_install_node_module({ project_name: row.name, mod_name: _mname }, function (res) {
					bt.msg({ status: res.status, msg: res.data || res.error_msg });
					node_project_module_table.$refresh_table_list(true);
				});
			});
			//一键安装项目模块
			$('.npm_install_node_config').on('click', function () {
				var _command = that.request_module_log_command({ shell: 'tail -f /www/server/panel/logs/npm-exec.log' });
				that.install_node_project_packages({ project_name: row.name }, function (res) {
					if (res.status) {
						node_project_module_table.$refresh_table_list(true);
					}
					layer.close(_command);
					bt.msg({ status: res.status, msg: res.data || res.error_msg });
				});
			});
		},

		/**
		 * @description 渲染Node项目伪静态
		 * @param el {object} 当前element节点
		 * @param row {object} 当前项目数据
		 */
		reander_node_project_rewrite: function (el, row) {
			el.empty();
			if (row.project_config.bind_extranet === 0) {
				$('.mask_module').removeClass('hide').find('.node_mask_module_text:eq(1)').hide().prev().show();
				return false;
			}
			site.edit.get_rewrite_list({ name: 'node_' + row.name }, function () {
				$('.webedit-box .line:first').remove();
				$('[name=btn_save_to]').remove();
				$('.webedit-box .help-info-text li:first').remove();
			});
		},
		/**
		 * @description 渲染Node配置文件
		 * @param el {object} 当前element节点
		 * @param row {object} 当前项目数据
		 */
		reander_node_file_config: function (el, row) {
			el.empty();
			if (row.project_config.bind_extranet === 0) {
				$('.mask_module').removeClass('hide').find('.node_mask_module_text:eq(1)').hide().prev().show();
				return false;
			}
			site.edit.set_config({ name: 'node_' + row.name });
		},
		/**
		 * @description 渲染node项目使用情况
		 * @param el {object} 当前element节点
		 * @param row {object} 当前项目数据
		 */
		reander_node_service_condition: function (el, row) {
			if (!row.run) {
				el.html('').next().removeClass('hide');
				if (el.next().find('.node_mask_module_text').length === 1) {
					el.next()
						.find('.node_mask_module_text')
						.hide()
						.parent()
						.append(
							'<div class="node_mask_module_text">Please start the service first and try again,<a href="javascript:;" class="btlink" onclick="site.node.simulated_click(7)">Set service status</a></div>'
						);
				} else {
					el.next().find('.node_mask_module_text:eq(1)').show().prev().hide();
				}
				return false;
			}
			el.html(
				'<div class="line" style="padding-top: 0;"><span class="tname" style="width: 30px;text-align:left;padding-right: 5px;">PID</span><div class="info-r"><select class="bt-input-text mr5" name="node_project_pid"></select></div></div><div class="node_project_pid_datail"></div>'
			);
			var _option = '',
				tabelCon = '';
			for (var load in row.load_info) {
				if (row.load_info.hasOwnProperty(load)) {
					_option += '<option value="' + load + '">' + load + '</option>';
				}
			}
			var node_pid = $('[name=node_project_pid]');
			node_pid.html(_option);
			node_pid
				.change(function () {
					var _pid = $(this).val(),
						rdata = row['load_info'][_pid],
						fileBody = '',
						connectionsBody = '';
					for (var i = 0; i < rdata.open_files.length; i++) {
						var itemi = rdata.open_files[i];
						fileBody +=
							'<tr>' +
							'<td>' +
							itemi['path'] +
							'</td>' +
							'<td>' +
							itemi['mode'] +
							'</td>' +
							'<td>' +
							itemi['position'] +
							'</td>' +
							'<td>' +
							itemi['flags'] +
							'</td>' +
							'<td>' +
							itemi['fd'] +
							'</td>' +
							'</tr>';
					}
					for (var k = 0; k < rdata.connections.length; k++) {
						var itemk = rdata.connections[k];
						connectionsBody +=
							'<tr>' +
							'<td>' +
							itemk['client_addr'] +
							'</td>' +
							'<td>' +
							itemk['client_rport'] +
							'</td>' +
							'<td>' +
							itemk['family'] +
							'</td>' +
							'<td>' +
							itemk['fd'] +
							'</td>' +
							'<td>' +
							itemk['local_addr'] +
							'</td>' +
							'<td>' +
							itemk['local_port'] +
							'</td>' +
							'<td>' +
							itemk['status'] +
							'</td>' +
							'</tr>';
					}

					//     tabelCon = reand_table_config([
					//         [{"名称":rdata.name},{"PID":rdata.pid},{"状态":rdata.status},{"父进程":rdata.ppid}],
					//         [{"用户":rdata.user},{"Socket":rdata.connects},{"CPU":rdata.cpu_percent},{"线程":rdata.threads}],
					//         [{"内存":rdata.user},{"io读":rdata.connects},{"io写":rdata.cpu_percent},{"启动时间":rdata.threads}],
					//         [{"启动命令":rdata.user}],
					//     ])
					//
					// console.log(tabelCon)
					//
					//
					//     function reand_table_config(conifg){
					//         var html = '';
					//         for (var i = 0; i < conifg.length; i++) {
					//             var item = conifg[i];
					//             html += '<tr>';
					//             for (var j = 0; j < item; j++) {
					//                 var items = config[j],name = Object.keys(items)[0];
					//                 console.log(items,name)
					//                 html += '<td>'+  name +'</td><td>'+ items[name] +'</td>'
					//             }
					//             console.log(html)
					//             html += '</tr>'
					//         }
					//         return '<div class="divtable"><table class="table"><tbody>'+ html  +'</tbody></tbody></table></div>';
					//     }

					tabelCon =
						'<div class="divtable">' +
						'<table class="table">' +
						'<tbody>' +
						'<tr>' +
						'<th width="50">Name</th><td  width="100">' +
						rdata.name +
						'</td>' +
						'<th width="50">Status</th><td  width="90">' +
						rdata.status +
						'</td>' +
						'<th width="60">User</th><td width="100">' +
						rdata.user +
						'</td>' +
						'<th width="80">Start Time</th><td width="150">' +
						getLocalTime(rdata.create_time) +
						'</td>' +
						'</tr>' +
						'<tr>' +
						'<th>PID</th><td  >' +
						rdata.pid +
						'</td>' +
						'<th>PPID</th><td >' +
						rdata.ppid +
						'</td>' +
						'<th>Thread</th><td>' +
						rdata.threads +
						'</td>' +
						'<th>Socket</th><td>' +
						rdata.connects +
						'</td>' +
						'</tr>' +
						'<tr>' +
						'<th>CPU</th><td>' +
						rdata.cpu_percent +
						'%</td>' +
						'<th>RAM</th><td>' +
						ToSize(rdata.memory_used) +
						'</td>' +
						'<th>Disk/R</th><td>' +
						ToSize(rdata.io_read_bytes) +
						'</td>' +
						'<th>Dis/W</th><td>' +
						ToSize(rdata.io_write_bytes) +
						'</td>' +
						'</tr>' +
						'<tr>' +
						'</tr>' +
						'<tr>' +
						'<th width="50">Command</th><td colspan="7" style="word-break: break-word;width: 570px">' +
						rdata.exe +
						'</td>' +
						'</tr>' +
						'</tbody>' +
						'</table>' +
						'</div>' +
						'<h3 class="tname">Network</h3>' +
						'<div class="divtable" >' +
						'<div style="height:160px;overflow:auto;border:#ddd 1px solid" id="nodeNetworkList">' +
						'<table class="table table-hover" style="border:none">' +
						'<thead>' +
						'<tr>' +
						'<th>Client address</th>' +
						'<th>Client port</th>' +
						'<th>Protocol</th>' +
						'<th>FD</th>' +
						'<th>local address</th>' +
						'<th>local port</th>' +
						'<th>Status</th>' +
						'</tr>' +
						'</thead>' +
						'<tbody>' +
						connectionsBody +
						'</tbody>' +
						'</table>' +
						'</div>' +
						'</div>' +
						'<h3 class="tname">Open files</h3>' +
						'<div class="divtable" >' +
						'<div style="height:160px;overflow:auto;border:#ddd 1px solid" id="nodeFileList">' +
						'<table class="table table-hover" style="border:none">' +
						'<thead>' +
						'<tr>' +
						'<th>Files</th>' +
						'<th>mode</th>' +
						'<th>position</th>' +
						'<th>flags</th>' +
						'<th>fd</th>' +
						'</tr>' +
						'</thead>' +
						'<tbody>' +
						fileBody +
						'</tbody>' +
						'</table>' +
						'</div>' +
						'</div>';
					$('.node_project_pid_datail').html(tabelCon);
					bt_tools.$fixed_table_thead('#nodeNetworkList');
					bt_tools.$fixed_table_thead('#nodeFileList');
				})
				.change()
				.html(_option);
		},

		/**
		 * @description 渲染Node项目日志
		 * @param el {object} 当前element节点
		 * @param row {object} 当前项目数据
		 */
		reander_node_project_log: function (el, row) {
			el.html('<div class="node_project_log"></div>');
			bt_tools.send(
				{
					url: '/project/nodejs/get_project_log',
					type: 'GET',
					data: { data: JSON.stringify({ project_name: row.name }) },
				},
				function (res) {
					$('#webedit-con .node_project_log').html('<pre class="command_output_pre" style="height:640px;">' + (typeof res == 'object' ? res.error_msg : res) + '</pre>');
					$('.command_output_pre').scrollTop($('.command_output_pre').prop('scrollHeight'));
				},
				{ load: 'Get Node project log', verify: false }
			);
		},

		reander_node_site_log: function (el, row) {
			el.empty();
			if (row.project_config.bind_extranet === 0) {
				$('.mask_module').removeClass('hide').find('.node_mask_module_text:eq(1)').hide().prev().show();
				return false;
			}
			site.edit.get_site_logs({ name: row.name });
		},

		/**
		 * @description node项目SSL
		 * @param el {object} 当前element节点
		 * @param row {object} 当前项目数据
		 */
		reander_node_project_ssl: function (el, row) {
			el.empty();
			if (row.project_config.bind_extranet === 0) {
				$('.mask_module').removeClass('hide').find('.node_mask_module_text:eq(1)').hide().prev().show();
				return false;
			}
			site.set_ssl({ name: row.name, ele: el, id: row.id });
			site.ssl.reload();
		},
		/**
		 * @description 请求模块日志终端
		 * @param config {object} 当前配置数据
		 */
		request_module_log_command: function (config) {
			var r_command = layer.open({
				title: config.name || 'Module is being installed, please wait...',
				type: 1,
				closeBtn: 0,
				area: ['500px', '342px'],
				skin: config.class || 'module_commmand',
				shadeClose: false,
				content: '<div class="site_module_command"></div>',
				success: function () {
					bt_tools.command_line_output({
						el: '.site_module_command',
						shell: config.shell,
						area: config.area || ['100%', '300px'],
					});
				},
			});
			return r_command;
		},

		/**
		 * @description 请求封装
		 * @param keyMethod 接口名和loading，键值对
		 * @param param {object || function} 参数，可为空，为空则为callback参数
		 * @param callback {function} 成功回调函数
		 * @param callback1 {function} 错误调函数
		 */
		http: function (keyMethod, param, callback, callback1) {
			var method = Object.keys(keyMethod),
				config = {
					url: '/project/nodejs/' + method[0],
					data: (param && { data: JSON.stringify(param) }) || {},
				},
				success = function (res) {
					callback && callback(res);
				};
			if (callback1) {
				bt_tools.send(config, success, callback1, {
					load: keyMethod[method[0]],
					verify: method[1] ? keyMethod[method[1]] : true,
				});
			} else {
				bt_tools.send(config, success, {
					load: keyMethod[method[0]],
					verify: method[1] ? keyMethod[method[1]] : true,
				});
			}
		},
	},
	node_porject_view: function () {
		var node_table = bt_tools.table({
			el: '#bt_node_table',
			url: '/project/nodejs/get_project_list',
			minWidth: '1000px',
			autoHeight: true,
			default: 'The item list is empty', //数据为空时的默认提示\
			load: 'Getting the list of Node projects, please wait...',
			beforeRequest: function (params) {
				if (params.hasOwnProperty('data') && typeof params.data === 'string') {
					var oldParams = JSON.parse(params['data']);
					delete params['data'];
					return { data: JSON.stringify($.extend(oldParams, params)) };
				}
				return { data: JSON.stringify(params) };
			},
			column: [
				{ type: 'checkbox', class: '', width: 20 },
				{
					fid: 'name',
					title: 'Name',
					width: 85,
					type: 'link',
					event: function (row, index, ev) {
						site.node.set_node_project_view(row);
					},
					template: function (row, index) {
						return (
							'<a class="btlink" style="display: inline-block; width: 90px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" href="javascript:;" title="' +
							row.name +
							'">' +
							row.name +
							'</a>'
						);
					},
				},
				{
					fid: 'run',
					title: 'Status',
					width: 85,
					config: {
						icon: true,
						list: [
							[true, 'Running', 'bt_success', 'glyphicon-play'],
							[false, 'Stop', 'bt_danger', 'glyphicon-pause'],
						],
					},
					type: 'status',
					event: function (row, index, ev, key, that) {
						var status = row.run;
						bt.confirm(
							{
								title: status ? 'Stop project' : 'Startup project',
								msg: status ? 'After stopping the project, the project service will stop running, continue?' : 'Startup Node project [' + row.name + '], continue operation?',
							},
							function (index) {
								layer.close(index);
								site.node[status ? 'stop_node_project' : 'start_node_project']({ project_name: row.name }, function (res) {
									bt.msg({ status: res.status, msg: res.data || res.error_msg });
									that.$refresh_table_list(true);
								});
							}
						);
					},
				},
				{
					fid: 'pid',
					title: 'PID',
					width: 180,
					type: 'text',
					template: function (row) {
						if ($.isEmptyObject(row['load_info'])) return '<span>-</span>';
						var _id = [];
						for (var i in row.load_info) {
							if (row.load_info.hasOwnProperty(i)) {
								_id.push(i);
							}
						}
						return '<span class="size_ellipsis" style="width:180px" title="' + _id.join(',') + '">' + _id.join(',') + '</span>';
					},
				},
				{
					title: 'CPU',
					type: 'text',
					template: function (row) {
						if ($.isEmptyObject(row['load_info'])) return '<span>-</span>';
						var _cpu_total = 0;
						for (var i in row.load_info) {
							_cpu_total += row.load_info[i]['cpu_percent'];
						}
						return '<span>' + _cpu_total.toFixed(2) + '%</span>';
					},
				},
				{
					title: 'RAM',
					type: 'text',
					template: function (row) {
						if ($.isEmptyObject(row['load_info'])) return '<span>-</span>';
						var _cpu_total = 0;
						for (var i in row.load_info) {
							_cpu_total += row.load_info[i]['memory_used'];
						}
						return '<span>' + bt.format_size(_cpu_total) + '</span>';
					},
				},
				{
					fid: 'path',
					title: 'Root directory',
					tips: 'Open Directory',
					type: 'link',
					event: function (row, index, ev) {
						openPath(row.path);
					},
					template: function (row, index) {
						return (
							'<a class="btlink" style="display: inline-block; width: 120px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" href="javascript:;" title="' +
							row.path +
							'">' +
							row.path +
							'</a>'
						);
					},
				},
				{
					fid: 'node_version',
					title: 'Node version',
					type: 'text',
					width: 102,
					template: function (row) {
						return '<span>' + row['project_config']['nodejs_version'] + '</span>';
					},
				},
				{
					fid: 'ps',
					title: 'Remark',
					type: 'input',
					blur: function (row, index, ev, key, that) {
						if (row.ps == ev.target.value) return false;
						bt.pub.set_data_ps({ id: row.id, table: 'sites', ps: ev.target.value }, function (res) {
							bt_tools.msg(res, { is_dynamic: true });
						});
					},
					keyup: function (row, index, ev) {
						if (ev.keyCode === 13) {
							$(this).blur();
						}
					},
				},
				{
					fid: 'ssl',
					title: 'SSL',
					tips: 'Deployment certificate',
					width: 100,
					type: 'text',
					template: function (row, index) {
						var _ssl = row.ssl,
							_info = '',
							_arry = [
								['issuer', 'issuer'],
								['notAfter', 'Due date'],
								['notBefore', 'Application date'],
								['dns', 'Available domain names'],
							];
						try {
							if (typeof row.ssl.endtime != 'undefined') {
								if (row.ssl.endtime < 0) {
									return '<a class="btlink bt_danger" href="javascript:;">Exp in ' + Math.row.ssl.endtime + ' days</a>';
								}
							}
						} catch (error) {}
						for (var i = 0; i < _arry.length; i++) {
							var item = _ssl[_arry[i][0]];
							_info += _arry[i][1] + ':' + item + (_arry.length - 1 != i ? '\n' : '');
						}
						return row.ssl === -1
							? '<a class="btlink bt_warning" href="javascript:;">Not Set</a>'
							: '<a class="btlink ' + (row.ssl.endtime < 7 ? 'bt_danger' : '') + '" href="javascript:;" title="' + _info + '">Exp in ' + row.ssl.endtime + ' days</a>';
					},
					event: function (row) {
						site.node.set_node_project_view(row);
						setTimeout(function () {
							$('.site-menu p:eq(5)').click();
						}, 500);
					},
				},
				{
					title: 'OPT',
					type: 'group',
					width: 100,
					align: 'right',
					group: [
						{
							title: 'Set',
							event: function (row, index, ev, key, that) {
								site.node.set_node_project_view(row);
							},
						},
						{
							title: 'Del',
							event: function (row, index, ev, key, that) {
								bt.prompt_confirm('Delete item', 'You are deleting the Node project-[' + row.name + '], continue?', function () {
									site.node.remove_node_project({ project_name: row.name }, function (res) {
										bt.msg({ status: res.status, msg: res.data || res.error_msg });
										node_table.$refresh_table_list(true);
									});
								});
							},
						},
					],
				},
			],
			sortParam: function (data) {
				return { order: data.name + ' ' + data.sort };
			},
			// 渲染完成
			tootls: [
				{
					// 按钮组
					type: 'group',
					positon: ['left', 'top'],
					list: [
						{
							title: 'Add Node project',
							active: true,
							event: function (ev) {
								site.node.add_node_form(function (res, index) {
									if (res.status) {
										layer.close(index);
										node_table.$refresh_table_list(true);
									}
									bt.msg({
										status: res.status,
										msg: (!Array.isArray(res.data) ? res.data : false) || res.error_msg,
									});
								});
							},
						},
						{
							title: 'Node version manager',
							event: function (ev) {
								bt.soft.set_lib_config('nodejs', 'Node.js version manager');
							},
						},
					],
				},
				{
					// 搜索内容
					type: 'search',
					positon: ['right', 'top'],
					placeholder: 'Please enter the project name',
					searchParam: 'search', //搜索请求字段，默认为 search
					value: '', // 当前内容,默认为空
				},
				{
					// 批量操作
					type: 'batch', //batch_btn
					positon: ['left', 'bottom'],
					placeholder: 'Please select bulk operation',
					buttonValue: 'Batch operation',
					disabledSelectValue: 'Please select the site that needs batch operation!',
					selectList: [
						{
							title: 'Delete item',
							url: '/project/nodejs/remove_project',
							param: function (row) {
								return {
									data: JSON.stringify({ project_name: row.name }),
								};
							},
							refresh: true,
							callback: function (that) {
								bt.prompt_confirm('Delete items in bulk', 'You are deleting the selected Node project. Continue?', function () {
									that.start_batch({}, function (list) {
										var html = '';
										for (var i = 0; i < list.length; i++) {
											var item = list[i];
											html +=
												'<tr><td><span>' +
												item.name +
												'</span></td><td><div style="float:right;"><span style="color:' +
												(item.requests.status ? '#20a53a' : 'red') +
												'">' +
												(item.requests.status ? item.requests.data : item.requests.error_msg) +
												'</span></div></td></tr>';
										}
										node_table.$batch_success_table({
											title: 'Delete items in bulk',
											th: 'project name',
											html: html,
										});
										node_table.$refresh_table_list(true);
									});
								});
							},
						},
					],
				},
				{
					//分页显示
					type: 'page',
					positon: ['right', 'bottom'], // 默认在右下角
					pageParam: 'p', //分页请求字段,默认为 : p
					page: 1, //当前分页 默认：1
					numberParam: 'limit',
					//分页数量请求字段默认为 : limit
					number: 20,
					//分页数量默认 : 20条
					numberList: [10, 20, 50, 100, 200], // 分页显示数量列表
					numberStatus: true, //　是否支持分页数量选择,默认禁用
					jump: true, //是否支持跳转分页,默认禁用
				},
			],
		});
	},
	php_table_view: function () {
		var hoverInfo = {};
		$('#bt_site_table').empty();

		$('.site_table_view').after(
			'<div class=" web_name_hover hide">\
						<div class=" web_name_title"></div>\
						<div class="web_name_setting ">\
							<span class="web_name_copy flex align-center btlink"><span class="web_name_copy_icon"></span>' +
				lan.site.copy +
				'<span id="site_name_copy"></span></span>\
							<span class="web_name_rename flex align-center btlink"><span class="web_name_rename_icon"></span>' +
				lan.site.rename +
				'</span>\
						</div>\
					</div>'
		);

		// 点击复制网站
		$('.web_name_copy')
			.unbind()
			.click(function (e) {
				var clipboard = new ClipboardJS('#site_name_copy');
				clipboard.on('success', function (e) {
					bt.msg({
						msg: lan.mail_sys.success_copy,
						icon: 1,
					});
				});
				clipboard.on('error', function (e) {
					bt.msg({
						msg: lan.pgsql.cp_fail,
						icon: 2,
					});
				});
				$('#site_name_copy').attr('data-clipboard-text', hoverInfo.site);
				$('#site_name_copy').click(function (e) {
					e.stopPropagation();
				});
				$('#site_name_copy').click();
			});

		// 点击重命名网站
		$('.web_name_rename')
			.unbind()
			.click(function (e) {
				var site_name = hoverInfo.site,
					site_id = hoverInfo.id;
				$(this)
					.parent()
					.prev()
					.find('.web_name_text')
					.html('<input type="text" title="' + lan.site.website_edit_tips + '" class="web_name_input" value="' + site_name + '"/>')
					.find('input')
					.focus()
					.click(function (e) {
						e.stopPropagation();
					});
				$(this)
					.parent()
					.prev()
					.find('.web_name_text')
					.find('input')
					.blur(function () {
						var new_name = $(this).val();
						if (new_name == site_name) {
							$('.web_name_hover').addClass('hide');
							return;
						}
						if (new_name != '') {
							bt_tools.send(
								{
									url: '/site?action=site_rname',
									data: { id: site_id, rname: escapeXml(new_name) },
								},
								function (res) {
									site_table.$refresh_table_list(true);
									bt.msg(res);
									$('.web_name_hover').addClass('hide');
								}
							);
						}
					});
				$(this)
					.parent()
					.prev()
					.find('.web_name_text')
					.find('input')
					.keyup(function (e) {
						if (e.keyCode == 13) {
							$(this).blur();
						}
					});
				// 防止网站xss
				function escapeXml(unsafe) {
					return unsafe.replace(/[<>&'"]/g, function (c) {
						switch (c) {
							case '<':
								return '&lt;';
							case '>':
								return '&gt;';
							case '&':
								return '&amp;';
							case "'":
								return '&apos;';
							case '"':
								return '&quot;';
						}
					});
				}
				e.stopPropagation();
			});

		site_table = bt_tools.table({
			el: '#bt_site_table',
			url: '/data?action=getData',
			cookiePrefix: 'site_table', // cookie前缀，用于状态存储，如果不设置，着所有状态不存储，
			param: { table: 'sites' }, //参数
			minWidth: '1000px',
			autoHeight: true,
			default: 'Site list is empty', // 数据为空时的默认提示
			beforeRequest: function (param) {
				param.type = bt.get_cookie('site_type') || -1;
				return param;
			},
			column: [
				{ type: 'checkbox', class: '', width: 20 },
				{
					fid: 'rname',
					title: lan.site.site_name,
					sort: true,
					sortValue: 'asc',
					class: 'site_name',
					type: 'link',
					width: 130,
					isDisabled: true,
					event: function (row, index, ev) {
						site.web_edit(row, true);
					},
					// template: function (row, index) {
					//     return '<div style="display: flex;"><a class="btlink size_ellipsis" style="flex: 1; width: 0;" title="' + row.name + '">' + row.name + '</a></div>';
					// }
					template: function (row, index) {
						var install = false;
						var recomConfig = product_recommend.get_recommend_type(5);
						if (recomConfig) {
							for (var j = 0; j < recomConfig['list'].length; j++) {
								var item = recomConfig['list'][j];
								if (item.name == 'btwaf' || item.name == 'btwaf_httpd') {
									if (item.install === true) install = true;
								}
							}
						}
						if (bt.get_cookie('serverType') == 'openlitespeed') {
							return (
								'<div style="display:inline-flex;align-items:center;position:relative">\
												<a class="btlink web_name" data-type="' +
								row.rname +
								'" data-name="' +
								row.name +
								'" data-id="' +
								row.id +
								'" href="javascript:;">' +
								row.rname +
								'</a>\
												</div>'
							);
						} else {
							var color = !$.isEmptyObject(row.waf) && row.waf.status && install ? 'green' : 'grey';
							return (
								'<div style="display:inline-flex;align-items:center;position:relative">\
																	<span title="WAF防火墙，保护网站安全" class="site_waf_icon_' +
								color +
								' site_waf_icon" data-id="' +
								row.id +
								'" data-type="' +
								row.rname +
								'" data-name="' +
								row.name +
								'" id="site_waf_icon' +
								index +
								'"></span>\
																	<a class="btlink web_name" data-type="' +
								row.rname +
								'" data-name="' +
								row.name +
								'" data-id="' +
								row.id +
								'" href="javascript:;">' +
								row.rname +
								'</a>\
																	\
																</div>'
							);
						}
					},
				},
				{
					fid: 'status',
					title: lan.site.status,
					sort: true,
					width: 85,
					config: {
						icon: true,
						list: [
							['1', lan.site.running_text, 'bt_success', 'glyphicon-play'],
							['0', lan.site.stopped, 'bt_danger', 'glyphicon-pause'],
						],
					},
					type: 'status',
					event: function (row, index, ev, key, that) {
						bt.site[parseInt(row.status) ? 'stop' : 'start'](row.id, row.name, function (res) {
							if (res.status) that.$modify_row_data({ status: parseInt(row.status) ? '0' : '1' });
						});
					},
				},
				{
					fid: 'backup_count',
					title: lan.site.backup,
					width: 80,
					type: 'link',
					template: function (row, index) {
						var backup = lan.site.backup_no,
							_class = 'bt_warning';
						if (row.backup_count > 0) (backup = lan.site.backup_yes), (_class = 'bt_success');
						return '<a href="javascript:;" class="btlink  ' + _class + '">' + backup + (row.backup_count > 0 ? '(' + row.backup_count + ')' : '') + '</a>';
					},
					event: function (row, index) {
						site.backup_site_view({ id: row.id, name: row.name }, site_table);
					},
				},
				{
					fid: 'path',
					title: lan.site.root_dir,
					tips: 'Open path',
					type: 'link',
					event: function (row, index, ev) {
						openPath(row.path);
					},
					template: function (row, index) {
						return '<div style="display: flex;"><a class="btlink size_ellipsis" style="flex: 1; width: 0;" href="javascript:;" title="' + row.path + '">' + row.path + '</a></div>';
					},
				},
				bt.public.get_quota_config('site'),
				{
					fid: 'edate',
					title: lan.site.endtime,
					width: 115,
					class: 'set_site_edate',
					sort: true,
					type: 'link',
					template: function (row, index) {
						var _endtime = row.edate || row.endtime;
						if (_endtime === '0000-00-00') {
							return lan.site.web_end_time;
						} else {
							if (new Date(_endtime).getTime() < new Date().getTime()) {
								return '<a href="javascript:;" class="bt_danger">' + _endtime + '</a>';
							} else {
								return _endtime;
							}
						}
					},
					event: function (row) {},
				},
				{
					fid: 'ps',
					title: lan.site.note,
					type: 'input',
					blur: function (row, index, ev) {
						if (row.ps == ev.target.value) return false;
						bt.pub.set_data_ps({ id: row.id, table: 'sites', ps: ev.target.value }, function (res) {
							if (!res.status) layer.msg(res.msg, { status: 2 });
						});
					},
					keyup: function (row, index, ev) {
						if (ev.keyCode === 13) {
							$(this).blur();
						}
					},
				},
				{
					fid: 'php_version',
					title: 'PHP',
					tips: 'Selete php version',
					width: 57,
					type: 'link',
					template: function (row, index) {
						if (row.php_version.indexOf('static') > -1) return row.php_version;
						return row.php_version;
					},
					event: function (row, index) {
						site.web_edit(row);
						setTimeout(function () {
							$('.site-menu p:eq(9)').click();
						}, 500);
					},
				},
				{
					fid: 'site_ssl',
					title: 'SSL',
					tips: 'Deployment certificate',
					width: 130,
					sort: true,
					type: 'text',
					template: function (row, index) {
						var _ssl = row.ssl,
							_info = '',
							_arry = [
								['issuer', 'Certificate'],
								['notAfter', 'Due date'],
								['notBefore', 'Application date'],
								['dns', 'Domain name'],
							];
						try {
							if (typeof row.ssl.endtime != 'undefined') {
								if (row.ssl.endtime < 0) {
									return '<a class="btlink bt_danger" href="javascript:;">Exp in ' + Math.row.ssl.endtime + ' days</a>';
								}
							}
						} catch (error) {}
						for (var i = 0; i < _arry.length; i++) {
							var item = _ssl[_arry[i][0]];
							_info += _arry[i][1] + ':' + item + (_arry.length - 1 != i ? '\n' : '');
						}
						return row.ssl === -1
							? '<a class="btlink bt_warning" href="javascript:;">Not Set</a>'
							: '<a class="btlink ' + (row.ssl.endtime < 7 ? 'bt_danger' : '') + '" href="javascript:;" title="' + _info + '">Exp in ' + row.ssl.endtime + ' days</a>';
					},
					event: function (row, index, ev, key, that) {
						//   console.log(row, '111');
						site.web_edit(row);
						setTimeout(function () {
							$('.site-menu p:eq(8)').click();
						}, 500);
					},
				},
				{
					fid: 'attack',
					title: 'Attack',
					width: 80,
					type: 'text',
					template: function (row, index) {
						return '<a class="btlink' + (row.attack > 0 ? ' bt_danger' : '') + '" style="cursor: pointer;">' + row.attack + '</a>';
					},
					event: function (row) {
						site.web_edit(row);
						setTimeout(function () {
							$('.site-menu p:eq(' + ($('.site-menu p').length - 1) + ')').click();
							setTimeout(function () {
								$('#tabLogs span:eq(2)').click();
							}, 500);
						}, 500);
					},
				},
				{
					title: lan.site.operate,
					type: 'group',
					width: 140,
					align: 'right',
					group: [
						{
							title: 'WAF',
							event: function (row, index, ev, key, that) {
								site.site_waf(row.name);
							},
						},
						{
							title: lan.site.set,
							event: function (row, index, ev, key, that) {
								site.web_edit(row, true);
							},
						},
						{
							title: 'Del',
							event: function (row, index, ev, key, that) {
								site.del_site(row.id, row.name, function () {
									that.$refresh_table_list(true);
								});
							},
						},
					],
				},
			],
			sortParam: function (data) {
				return { order: data.name + ' ' + data.sort };
			},
			// 表格渲染完成后
			success: function (that) {
				$('.event_edate_' + that.random).each(function () {
					var $this = $(this);
					laydate.render({
						elem: $this[0], //指定元素
						min: bt.get_date(1),
						max: '2099-12-31',
						vlue: bt.get_date(365),
						type: 'date',
						format: 'yyyy-MM-dd',
						trigger: 'click',
						btns: ['perpetual', 'confirm'],
						theme: '#20a53a',
						ready: function () {
							$this.click();
						},
						done: function (date) {
							var item = that.event_rows_model.rows;
							bt.site.set_endtime(item.id, date, function (res) {
								if (res.status) {
									layer.msg(res.msg);
									return false;
								}
								bt.msg(res);
							});
						},
					});
				});
				if ($('#bt_site_table table thead th:eq(9) a').length == 0) {
					var Attack_tips =
						'<ul class="help-info-text c7">\
                      <li>Log analysis: Scan the logs(/www/wwwroot/.log) for requests with attack (types include:<em style="color:red">xss,sql,san,php</em>)</li>\
                      <li>Analyzed log data contains intercepted requests</li>\
                      <li>By default, the last scan data is displayed (if not, please click log scan)</li>\
                      <li>If the log file is too large, scanning may take a long time, please be patient</li>\
                      <li><a class="btlink" href="https://www.aapanel.com/forum/d/3351-nginx-waf-instructions" target="_blank">aaPanel WAF</a> can effectively block such attacks</li>\
                      </ul>';
					$('#bt_site_table table thead th:eq(9)>span').css({ width: '42px', display: 'initial' }); //设置扫描th大小
					//追加tips并设置样式
					$('#bt_site_table table thead th:eq(9)').append(
						$('<a class="bt-ico-ask">?</a>')
							.css({ 'border-color': '#666', color: '#666' })
							.hover(
								function () {
									$(this).css({ 'border-color': '#fb7d00', color: '#fff' });
									layer.tips(Attack_tips, $(this), { time: 0, tips: [1, '#fff'], area: ['500px', '180px'] });
								},
								function () {
									$(this).css({ 'border-color': '#666', color: '#666' });
									layer.closeAll('tips');
								}
							)
					);
				}

				$('.web_name').hover(
					function (e) {
						if ($('.web_name_input').is(':focus')) return;
						// 获取元素基于浏览器的位置
						function getElementPosition(element) {
							let top = element.offsetTop; //这是获取元素距父元素顶部的距离
							let left = element.offsetLeft;
							var current = element.offsetParent; //这是获取父元素
							while (current !== null) {
								//当它上面有元素时就继续执行
								top += current.offsetTop; //这是获取父元素距它的父元素顶部的距离累加起来
								left += current.offsetLeft;
								current = current.offsetParent; //继续找父元素
							}
							return {
								top,
								left,
							};
						}
						hoverInfo['site'] = $(this).data('type');
						hoverInfo['id'] = $(this).data('id');
						$('.web_name_hover')
							.find('.web_name_title')
							.html(lan.site.website_name + '<span class="web_name_text">' + $(this).data('type') + '</span>');
						var _that = $(this);
						$('.web_name_hover').css({ left: getElementPosition(e.target).left - 110 + _that.width() / 2 + 'px', top: getElementPosition(e.target).top - 80 + 'px' });
						$('.web_name_hover').removeClass('hide');
					},
					function (e) {
						$('.web_name_hover').hover(
							function () {
								// 鼠标进入web_name_hover时显示
								$(this).removeClass('hide');
							},
							function () {
								if ($('.web_name_input').is(':focus')) return;
								// 鼠标离开web_name_hover时隐藏
								$(this).addClass('hide');
							}
						);
						$('.site_name')
							.parent()
							.mouseleave(function () {
								if ($('.web_name_input').is(':focus')) return;
								$('.web_name_hover').addClass('hide');
							});
					}
				);
			},
			// 渲染完成
			tootls: [
				{
					// 按钮组
					type: 'group',
					positon: ['left', 'top'],
					list: [
						{
							title: 'Add site',
							active: true,
							event: function (ev) {
								site.add_site(function (res, param) {
									var id = bt.get_cookie('site_type');
									if (param) {
										// 创建站点
										if (id != -1 && id != param.type_id) {
											$('#php_cate_select .bt_select_list .item.active').click();
										} else {
											site_table.$refresh_table_list(true);
										}
									} else {
										// 批量添加
										$('#php_cate_select .bt_select_list li[data-id="-1"]').click();
									}
								});
							},
						},
						{
							title: 'Default Page',
							event: function (ev) {
								site.set_default_page();
							},
						},
						{
							title: 'Default Website',
							event: function (ev) {
								site.set_default_site();
							},
						},
						{
							title: 'PHP CLI version',
							event: function (ev) {
								site.get_cli_version();
							},
						},
					],
				},
				{
					// 搜索内容
					type: 'search',
					positon: ['right', 'top'],
					placeholder: 'Domain or Remarks',
					searchParam: 'search', //搜索请求字段，默认为 search
					value: '', // 当前内容,默认为空
				},
				{
					// 批量操作
					type: 'batch', //batch_btn
					positon: ['left', 'bottom'],
					placeholder: 'Select batch operation',
					buttonValue: 'Execute',
					disabledSelectValue: 'Select the website to execute!',
					selectList: [
						{
							group: [
								{ title: lan.site.enable_website, param: { status: 1 } },
								{
									title: 'Disable website',
									param: { status: 0 },
								},
							],
							url: '/site?action=set_site_status_multiple',
							confirmVerify: false, //是否提示验证方式
							paramName: 'sites_id', //列表参数名,可以为空
							paramId: 'id', // 需要传入批量的id
							theadName: 'Name',
							refresh: true,
						},
						{
							title: lan.site.backup_website,
							url: '/site?action=ToBackup',
							paramId: 'id',
							load: true,
							theadName: 'Name',
							refresh: true,
							callback: function (that) {
								// 手动执行,data参数包含所有选中的站点
								that.start_batch({}, function (list) {
									var html = '';
									for (var i = 0; i < list.length; i++) {
										var item = list[i];
										html +=
											'<tr><td><span style="width: 150px;" class="limit-text-length" title="' +
											item.name +
											'">' +
											item.name +
											'</span></td><td class="text-right"><span style="color:' +
											(item.request.status ? '#20a53a' : 'red') +
											'">' +
											item.request.msg +
											'</span></td></tr>';
									}
									site_table.$batch_success_table({ title: 'Batch backup', th: 'Site name', html: html });
									site_table.$refresh_table_list(true);
								});
							},
						},
						{
							title: lan.site.set_expired,
							url: '/site?action=set_site_etime_multiple',
							paramName: 'sites_id', //列表参数名,可以为空
							paramId: 'id', // 需要传入批量的id
							theadName: 'Name',
							refresh: true,
							confirm: {
								title: 'Batch set expired date',
								content:
									'<div class="line"><span class="tname">Expired date</span><div class="info-r "><input name="edate" id="site_edate" class="bt-input-text mr5" placeholder="yyyy-MM-dd" type="text"></div></div>',
								success: function () {
									laydate.render({
										elem: '#site_edate',
										min: bt.format_data(new Date().getTime(), 'yyyy-MM-dd'),
										max: '2099-12-31',
										vlue: bt.get_date(365),
										type: 'date',
										format: 'yyyy-MM-dd',
										trigger: 'click',
										btns: ['perpetual', 'confirm'],
										theme: '#20a53a',
									});
								},
								yes: function (index, layers, request) {
									var site_edate = $('#site_edate'),
										site_edate_val = site_edate.val();
									if (site_edate_val != '') {
										request({ edate: site_edate_val === 'Forever' ? '0000-00-00' : site_edate_val });
									} else {
										layer.tips('Input expired date', '#site_edate', { tips: ['1', 'red'] });
										$('#site_edate').css('border-color', 'red');
										$('#site_edate').click();
										setTimeout(function () {
											$('#site_edate').removeAttr('style');
										}, 3000);
										return false;
									}
								},
							},
						},
						{
							title: lan.site.set_php_version,
							url: '/site?action=set_site_php_version_multiple',
							paramName: 'sites_id', //列表参数名,可以为空
							paramId: 'id', // 需要传入批量的id
							theadName: 'Name',
							refresh: true,
							confirm: {
								title: 'Batch set php version',
								area: '420px',
								content:
									'<div class="line"><span class="tname">PHP version</span><div class="info-r"><select class="bt-input-text mr5 versions" name="versions" style="width:150px"></select></span></div><ul class="help-info-text c7" style="font-size:11px"><li>Please select the version according to your program requirements.</li><li>If not necessary, please try not to use PHP 5.2, which will reduce your server security.</li><li>PHP 7 does not support mysql extension, mysqli and mysql_pdo will be installed by default.</li></ul></div>',
								success: function () {
									bt.site.get_all_phpversion(function (res) {
										var html = '';
										$.each(res, function (index, item) {
											html += '<option value="' + item.version + '">' + item.name + '</option>';
										});
										$('[name="versions"]').html(html);
									});
								},
								yes: function (index, layers, request) {
									request({ version: $('[name="versions"]').val() });
								},
							},
						},
						{
							title: lan.site.set_category,
							url: '/site?action=set_site_type',
							paramName: 'site_ids', //列表参数名,可以为空
							paramId: 'id', // 需要传入批量的id
							refresh: true,
							beforeRequest: function (list) {
								var arry = [];
								$.each(list, function (index, item) {
									arry.push(item.id);
								});
								return JSON.stringify(arry);
							},
							confirm: {
								title: 'Batch set category',
								content:
									'<div class="line"><span class="tname">Site category</span><div class="info-r"><select class="bt-input-text mr5 site_types" name="site_types" style="width:150px"></select></span></div></div>',
								success: function () {
									bt.site.get_type(function (res) {
										var html = '';
										$.each(res, function (index, item) {
											html += '<option value="' + item.id + '">' + item.name + '</option>';
										});
										$('[name="site_types"]').html(html);
									});
								},
								yes: function (index, layers, request) {
									request({ id: $('[name="site_types"]').val() });
								},
							},
							tips: false,
							refresh: true,
							success: function (res, list, that) {
								var html = '';
								$.each(list, function (index, item) {
									html += '<tr><td>' + item.name + '</td><td><div style="float:right;"><span style="color:' + (res.status ? '#20a53a' : 'red') + '">' + res.msg + '</span></div></td></tr>';
								});
								that.$batch_success_table({ title: 'Batch set category', th: 'Site name', html: html });
								that.$refresh_table_list(true);
							},
						},
						{
							title: lan.site.del_website,
							url: '/site?action=DeleteSite',
							// paramName:'sites_id', //列表参数名,可以为空
							// paramId:'id', //需要传入批量的id
							// theadName:'Name',
							refresh: true,
							param: function (row) {
								return {
									id: row.id,
									webname: row.name,
								};
							},
							load: true,
							callback: function (that) {
								// bt.show_confirm("Delete site","Confirm delete the FTP、database、root path of the selected site with the same name", function(){
								//     var param = {};
								//     $('.bacth_options input[type=checkbox]').each(function(){
								//         var checked = $(this).is(":checked");
								//         if(checked) param[$(this).attr('name')] = checked?1:0;
								//     })
								//     if(callback) callback(param);
								// },"<div class='options bacth_options'><span class='item'><label><input type='checkbox' name='ftp'><span>FTP</span></label></span><span class='item'><label><input type='checkbox' name='database'><span>" + lan.site.database + "</span></label></span><span class='item'><label><input type='checkbox' name='path'><span>" + lan.site.root_dir + "</span></label></span></div>");
								var ids = [];
								for (var i = 0; i < that.check_list.length; i++) {
									ids.push(that.check_list[i].id);
								}
								site.del_site(ids, function (param) {
									that.start_batch(param, function (list) {
										layer.closeAll();
										var html = '';
										for (var i = 0; i < list.length; i++) {
											var item = list[i];
											html +=
												'<tr><td><span style="width: 150px;" class="limit-text-length" title="' +
												item.name +
												'">' +
												item.name +
												'</span></td><td><div style="float:right;"><span style="color:' +
												(item.request.status ? '#20a53a' : 'red') +
												'">' +
												item.request.msg +
												'</span></div></td></tr>';
										}
										site_table.$batch_success_table({
											title: 'Batch delete',
											th: 'site name',
											html: html,
										});
										site_table.$refresh_table_list(true);
									});
								});
							},
						},
					],
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
		});

		this.init_site_type();
	},

	/**
	 * @description 初始化php分类和需求反馈
	 */
	init_site_type: function () {
		$('#php_cate_select').remove();
		$('.feedback-btn').remove();
		$('.tootls_group.tootls_top .pull-left').append(
			'\
			<div id="php_cate_select" class="bt_select_updown site_class_type" style="vertical-align: bottom;">\
					<div class="bt_select_value">\
						<span class="bt_select_content">Classification: </span><span class="glyphicon glyphicon-triangle-bottom ml5"></span>\
					</span>\
				</div>\
				<ul class="bt_select_list"></ul>\
			</div>\
			<span style="display:inline-block; margin-left:10px;vertical-align: bottom;" class="feedback-btn"><span class="flex" style="align-items: center;margin-right:16px;width:100px;"><i class="icon-demand"></i><a class="btlink" onClick="javascript:bt.openFeedback({title:\'aaPanel demand feedback collection\',placeholder:\'<span>If you encounter any problems or imperfect functions during use, please describe <br> your problems or needs to us in detail, we will try our best to solve or improve for <br> you</span>\',recover:\'We pay special attention to your requirements feedback, and we conduct regular weekly requirements reviews. I hope I can help you better\',key:993,proType:2});" style="margin-left: 5px;">Feedback</a></span></span>'
		);
		bt.site.get_type(function (res) {
			site.reader_site_type(res);
		});
	},
	reader_site_type: function (res, config) {
		var html = '',
			active = bt.get_cookie('site_type') || -1,
			select = $('#php_cate_select'),
			config = site_table;

		if (select.find('.bt_select_list li').length > 1) return false;

		res.unshift({ id: -1, name: 'Category manager' });

		$.each(res, function (index, item) {
			html += '<li class="item ' + (parseInt(active) == item.id ? 'active' : '') + '" data-id="' + item.id + '">' + item.name + '</li>';
		});

		html += '<li role="separator" class="divider"></li><li class="item" data-id="type_sets">Category set</li>';

		select.find('.bt_select_value').on('click', function (ev) {
			var $this = this;
			$(this).next().show();
			$(document).one('click', function () {
				$($this).next().hide();
			});
			ev.stopPropagation();
		});

		select
			.find('.bt_select_list')
			.unbind('click')
			.on('click', 'li', function () {
				var id = $(this).data('id');
				if (id === 'type_sets') {
					site.set_class_type();
				} else {
					bt.set_cookie('site_type', id);
					config.config.page.page = 1;
					config.$refresh_table_list(true);
					$(this).addClass('active').siblings().removeClass('active');
					// select.find('.bt_select_value .bt_select_content').text('Classification: ' + $(this).text());
					select.find('.bt_select_value .bt_select_content').text($(this).text());
				}
			})
			.empty()
			.html(html);

		select = $(select[0]);

		if (!select.find('.bt_select_list li.active').length) {
			select.find('.bt_select_list li:eq(0)').addClass('active');
			// select.find('.bt_select_value .bt_select_content').text('Classification: 默认分类');
			select.find('.bt_select_value .bt_select_content').text('Default category');
		} else {
			// select.find('.bt_select_value .bt_select_content').text('Classification: ' + select.find('.bt_select_list li.active').text());
			select.find('.bt_select_value .bt_select_content').text(select.find('.bt_select_list li.active').text());
		}
	},
	get_list: function (page, search, type) {
		if (page == undefined) page = 1;
		if (type == '-1' || type == undefined) {
			type = bt.get_cookie('site_type');
		}
		if (!search) search = $('#SearchValue').val();
		bt.site.get_list(page, search, type, function (rdata) {
			$('.dataTables_paginate').html(rdata.page);
			var data = rdata.data;
			var _tab = bt.render({
				table: '#webBody',
				columns: [
					{ field: 'id', type: 'checkbox', width: 30 },
					{
						field: 'name',
						title: lan.site.site_name,
						width: 150,
						templet: function (item) {
							return '<a class="btlink webtips" onclick="site.web_edit(this)" href="javascript:;">' + item.name + '</a>';
						},
						sort: function () {
							site.get_list();
						},
					},
					{
						field: 'status',
						title: lan.site.status,
						width: 98,
						templet: function (item) {
							var _status = '<a href="javascript:;" ';
							if (item.status == '1' || item.status == lan.site.normal || item.status == lan.site.running) {
								_status += ' onclick="bt.site.stop(' + item.id + ",'" + item.name + '\') " >';
								_status += '<span style="color:#5CB85C">' + lan.site.running_text + ' </span><span style="color:#5CB85C" class="glyphicon glyphicon-play"></span>';
							} else {
								_status += ' onclick="bt.site.start(' + item.id + ",'" + item.name + '\')"';
								_status += '<span style="color:red">' + lan.site.stopped + '  </span><span style="color:red" class="glyphicon glyphicon-pause"></span>';
							}
							return _status;
						},
						sort: function () {
							site.get_list();
						},
					},
					{
						field: 'backup',
						title: lan.site.backup,
						width: 105,
						templet: function (item) {
							var backup = lan.site.backup_no;
							if (item.backup_count > 0) backup = lan.site.backup_yes;
							return '<a href="javascript:;" class="btlink" onclick="site.site_detail(' + item.id + ",'" + item.name + '\')">' + backup + '</a>';
						},
					},
					{
						field: 'path',
						title: lan.site.root_dir,
						templet: function (item) {
							var _path = bt.format_path(item.path);
							return '<a class="btlink webPath" title="' + _path + '" href="javascript:openPath(\'' + _path + '\');">' + _path + '</a>';
						},
					},
					{
						field: 'edate',
						title: lan.site.endtime,
						width: 127,
						templet: function (item) {
							var _endtime = '';
							if (item.edate) _endtime = item.edate;
							if (item.endtime) _endtime = item.endtime;
							_endtime = _endtime == '0000-00-00' ? lan.site.web_end_time : _endtime;
							return '<a class="btlink setTimes" id="site_endtime_' + item.id + '" >' + _endtime + '</a>';
						},
						sort: function () {
							site.get_list();
						},
					},
					{
						field: 'ps',
						title: lan.site.note,
						templet: function (item) {
							return "<span class='c9 input-edit webPath'  onclick=\"bt.pub.set_data_by_key('sites','ps',this)\">" + item.ps + '</span>';
						},
					},
					{
						field: 'php_version',
						width: 70,
						title: 'PHP',
						templet: function (item) {
							return '<a class="phpversion_tips btlink">' + item.php_version + '</a>';
						},
					},
					{
						field: 'ssl',
						title: 'SSL',
						templet: function (item) {
							var _ssl = '';
							if (item.ssl == -1) {
								_ssl = '<a class="ssl_tips btlink" style="color:orange;">Not Set</a>';
							} else {
								var ssl_info = 'Certificate: ' + item.ssl.issuer + '<br>Due date: ' + item.ssl.notAfter + '<br>Application date: ' + item.ssl.notBefore + '<br>Domain name: ' + item.ssl.dns.join('/');
								if (item.ssl.endtime < 0) {
									_ssl = '<a class="ssl_tips btlink" style="color:red;" data-tips="' + ssl_info + '">Expired</a>';
								} else if (item.ssl.endtime < 20) {
									_ssl = '<a class="ssl_tips btlink" style="color:red;" data-tips="' + ssl_info + '">Exp in ' + (item.ssl.endtime + ' days') + '</a>';
								} else {
									_ssl = '<a class="ssl_tips btlink" style="color:green;" data-tips="' + ssl_info + '">Exp in ' + item.ssl.endtime + ' days</a>';
								}
							}
							return _ssl;
						},
					},
					{
						field: 'opt',
						width: 90,
						title: lan.site.operate,
						align: 'right',
						templet: function (item) {
							var opt = '';
							var _check = ' onclick="site.site_waf(\'' + item.name + '\')"';

							//if (bt.os == 'Linux') opt += '<a href="javascript:;" ' + _check + ' class="btlink ">' + lan.site.firewalld + '</a> | ';
							opt += '<a href="javascript:;" class="btlink" onclick="site.web_edit(this)">' + lan.site.set + ' </a> | ';
							opt += '<a href="javascript:;" class="btlink" onclick="site.del_site(' + item.id + ",'" + item.name + '\')" title="' + lan.site.del_site + '">' + lan.site.del + '</a>';
							return opt;
						},
					},
				],
				data: data,
			});
			var outTime = '';
			$('.ssl_tips').hover(
				function () {
					var that = this,
						tips = $(that).attr('data-tips');
					if (!tips) return false;
					outTime = setTimeout(function () {
						layer.tips(tips, $(that), {
							tips: [2, '#20a53a'], //还可配置颜色
							time: 0,
						});
					}, 500);
				},
				function () {
					outTime != '' ? clearTimeout(outTime) : '';
					layer.closeAll('tips');
				}
			);
			$('.ssl_tips').click(function () {
				site.web_edit(this);
				var timeVal = setInterval(function () {
					var content = $('#webedit-con').html();
					if (content != '') {
						$('.site-menu p:contains("SSL")').click();
						clearInterval(timeVal);
					}
				}, 100);
			});
			$('.phpversion_tips').click(function () {
				site.web_edit(this);
				var timeVal = setInterval(function () {
					var content = $('#webedit-con').html();
					if (content != '') {
						$('.site-menu p:contains("PHP version")').click();
						clearInterval(timeVal);
					}
				}, 100);
			});
			//浏览器窗口大小变化时调整内容宽度
			var ticket_with = $('#webBody').width(),
				td_width = (ticket_with - 667 - $('#webBody th:contains("SSL")').width()) / 2;
			$('#webBody .webPath').css('max-width', td_width);
			$(window).resize(function () {
				var ticket_with = $('#webBody').width(),
					td_width = (ticket_with - 667 - $('#webBody th:contains("SSL")').width()) / 2;
				$('#webBody .webPath').css('max-width', td_width);
			});
			//设置到期时间
			$('a.setTimes').each(function () {
				var _this = $(this);
				var _tr = _this.parents('tr');
				var id = _this.attr('id');
				laydate.render({
					elem: '#' + id, //指定元素
					lang: 'en',
					min: bt.get_date(1),
					max: '2099-12-31',
					vlue: bt.get_date(365),
					type: 'date',
					format: 'yyyy-MM-dd',
					trigger: 'click',
					btns: ['perpetual', 'confirm'],
					theme: '#20a53a',
					done: function (dates) {
						var item = _tr.data('item');
						bt.site.set_endtime(item.id, dates, function () {});
					},
				});
			});
			//})
		});
	},
	site_waf: function (siteName) {
		try {
			site_waf_config(siteName);
		} catch (err) {
			site.no_firewall();
		}
	},
	html_encode: function (html) {
		var temp = document.createElement('div');
		//2.然后将要转换的字符串设置为这个元素的innerText(ie支持)或者textContent(火狐，google支持)
		temp.textContent != undefined ? (temp.textContent = html) : (temp.innerText = html);
		//3.最后返回这个元素的innerHTML，即得到经过HTML编码转换的字符串了
		var output = temp.innerHTML;
		temp = null;
		return output;
	},
	get_types: function (callback) {
		bt.site.get_type(function (rdata) {
			var optionList = '';
			var t_val = bt.get_cookie('site_type');
			for (var i = 0; i < rdata.length; i++) {
				optionList += '<button class="btn btn-' + (t_val == rdata[i].id ? 'success' : 'default') + ' btn-sm" value="' + rdata[i].id + '">' + rdata[i].name + '</button>';
			}
			if ($('.dataTables_paginate').next().hasClass('site_type')) $('.site_type').remove();
			$('.dataTables_paginate').after(
				'<div class="site_type"><button class="btn btn-' + (t_val == '-1' ? 'success' : 'default') + ' btn-sm" value="-1">' + lan.site.all_classification + '</button>' + optionList + '</div>'
			);
			$('.site_type button').click(function () {
				var val = $(this).attr('value');
				bt.set_cookie('site_type', val);
				site.get_list(0, '', val);
				$('.site_type button').removeClass('btn-success').addClass('btn-default');
				$(this).addClass('btn-success');
			});
			if (callback) callback(rdata);
		});
	},
	no_firewall: function (obj) {
		var typename = bt.get_cookie('serverType');
		layer.confirm(
			lan.site.firewalld_nonactivated_tips.replace('{1}', typename).replace('{2}', typename),
			{
				title: typename + lan.site.site_classification,
				icon: 7,
				closeBtn: 2,
				cancel: function () {
					if (obj) $(obj).prop('checked', false);
				},
			},
			function () {
				window.location.href = '/soft';
			},
			function () {
				if (obj) $(obj).prop('checked', false);
			}
		);
	},
	site_detail: function (id, siteName, page) {
		if (page == undefined) page = '1';
		var loadT = bt.load(lan.public.the_get);
		bt.pub.get_data('table=backup&search=' + id + '&limit=5&type=0&tojs=site.site_detail&p=' + page, function (frdata) {
			loadT.close();
			var ftpdown = '';
			var body = '';
			var port;
			frdata.page = frdata.page.replace(/'/g, '"').replace(/site.site_detail\(/g, 'site.site_detail(' + id + ",'" + siteName + "',");
			if ($('#SiteBackupList').length <= 0) {
				bt.open({
					type: 1,
					skin: 'demo-class',
					area: '700px',
					title: lan.site.backup_title,
					closeBtn: 2,
					shift: 5,
					shadeClose: false,
					content:
						"<div class='divtable pd15 style='padding-bottom: 0'><button id='btn_data_backup' class='btn btn-success btn-sm' type='button' style='margin-bottom:10px'>" +
						lan.database.backup +
						"</button><table width='100%' id='SiteBackupList' class='table table-hover'></table><ul class='help-info-text c7'><li>Before restoring data, all data in the root dir of the website  will be moved to the panel recycle bin.</li></ul><div class='page sitebackup_page'></div></div>",
				});
			}
			setTimeout(function () {
				$('.sitebackup_page').html(frdata.page);
				var _tab = bt.render({
					table: '#SiteBackupList',
					columns: [
						{
							field: 'name',
							title: lan.site.filename,
							templet: function (item) {
								var _opt = '<span style="display: inline-block;max-width: 259px;overflow: hidden;text-overflow: ellipsis;" title="' + item.name + '">' + item.name + '</span>';
								return _opt;
							},
						},
						{
							field: 'size',
							title: lan.site.filesize,
							templet: function (item) {
								return bt.format_size(item.size);
							},
						},
						{ field: 'addtime', title: lan.site.backup_time },
						{
							field: 'opt',
							title: lan.site.operate,
							align: 'right',
							templet: function (item) {
								var _opt = '<a class="btlink restore" site-id="' + id + '" backup-name="' + item.name + '">Restore</a> | ';
								_opt += '<a class="btlink" href="/download?filename=' + item.filename + '&amp;name=' + item.name + '" target="_blank">' + lan.site.download + '</a> | ';
								_opt += '<a class="btlink" herf="javascrpit:;" onclick="bt.site.del_backup(\'' + item.id + "','" + id + "','" + siteName + '\')">' + lan.site.del + '</a>';
								return _opt;
							},
						},
					],
					data: frdata.data,
				});
				$('#btn_data_backup')
					.unbind('click')
					.click(function () {
						bt.site.backup_data(id, function (rdata) {
							if (rdata.status) site.site_detail(id, siteName);
							site.get_list();
						});
					});
				$('#SiteBackupList .restore')
					.unbind('click')
					.click(function () {
						var data = {};
						data.file_name = $(this).attr('backup-name');
						data.site_id = $(this).attr('site-id');
						// console.log(data);
						layer.confirm(
							'Are you sure to restore backup file?',
							{
								icon: 0,
								closeBtn: 2,
								title: 'Restore backup file',
							},
							function (index) {
								$.post('/files?action=restore_website', data, function (rdata) {
									layer.close(index);
									site.backup_output_stop = true;
									layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
								});
								site.backup_output_logs();
							}
						);
					});
			}, 100);
		});
	},
	/**
	 * @description 备份站点视图
	 * @param {object} config  配置参数
	 * @param {function} callback  回调函数
	 */
	backup_site_view: function (config, thatC, callback) {
		bt_tools.open({
			title: lan.site.backup_title + '&nbsp;-&nbsp;[&nbsp;' + config.name + '&nbsp;]',
			area: '720px',
			btn: false,
			skin: 'bt_backup_table',
			content: '<div id="bt_backup_table" class="pd20" style="padding-bottom:40px;"></div>',
			success: function ($layer) {
				var backup_table = bt_tools.table({
					el: '#bt_backup_table',
					url: '/data?action=getData',
					param: { table: 'backup', search: config.id, type: '0' },
					default: '[' + config.name + '] Currently no backup', //数据为空时的默认提示
					column: [
						{ type: 'checkbox', class: '', width: 20 },
						{ fid: 'name', title: lan.site.filename, width: 250, fixed: true },
						{
							fid: 'size',
							title: lan.site.filesize,
							width: 80,
							type: 'text',
							template: function (row, index) {
								return bt.format_size(row.size);
							},
						},
						{ fid: 'addtime', width: 150, title: lan.site.backup_time },
						{
							title: lan.site.operate,
							type: 'group',
							width: 165,
							align: 'right',
							group: [
								{
									title: 'Restore',
									event: function (row) {
										var data = {};
										data.file_name = row.name;
										data.site_id = config.id;
										// console.log(data);
										layer.confirm(
											'Are you sure to restore backup file?',
											{
												icon: 0,
												closeBtn: 2,
												title: 'Restore backup file',
											},
											function (index) {
												$.post('/files?action=restore_website', data, function (rdata) {
													layer.close(index);
													site.backup_output_stop = true;
													layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
												});
												site.backup_output_logs();
											}
										);
									},
								},
								{
									title: lan.site.download,
									template: function (row, index, ev, key, that) {
										return '<a target="_blank" class="btlink" href="/download?filename=' + row.filename + '&amp;name=' + row.name + '">' + lan.site.download + '</a>';
									},
								},
								{
									title: lan.site.del,
									event: function (row, index, ev, key, that) {
										that.del_site_backup({ name: row.name, id: row.id }, function (rdata) {
											bt_tools.msg(rdata);
											if (rdata.status) {
												thatC.$modify_row_data({ backup_count: thatC.event_rows_model.rows.backup_count - 1 });
												that.$refresh_table_list();
											}
										});
									},
								},
							],
						},
					],
					methods: {
						/**
						 * @description 删除站点备份
						 * @param {object} config
						 * @param {function} callback
						 */
						del_site_backup: function (config, callback) {
							bt.confirm(
								{
									title: lan.site.del_bak_file,
									msg: 'The website backup is about to be deleted [' + config.name + '], do you want to continue?',
								},
								function () {
									bt_tools.send(
										'site/DelBackup',
										{ id: config.id },
										function (rdata) {
											if (callback) callback(rdata);
										},
										true
									);
								}
							);
						},
					},
					success: function () {
						if (callback) callback();
						$('.bt_backup_table').css('top', ($(window).height() - $('.bt_backup_table').height()) / 2 + 'px');
					},
					tootls: [
						{
							// 按钮组
							type: 'group',
							positon: ['left', 'top'],
							list: [
								{
									title: 'Backup',
									active: true,
									event: function (ev, that) {
										bt.site.backup_data(config.id, function (rdata) {
											bt_tools.msg(rdata);
											if (rdata.status) {
												thatC.$modify_row_data({ backup_count: thatC.event_rows_model.rows.backup_count + 1 });
												that.$refresh_table_list();
											}
										});
									},
								},
							],
						},
						{
							type: 'batch',
							positon: ['left', 'bottom'],
							config: {
								title: ' Delete',
								url: '/site?action=DelBackup',
								paramId: 'id',
								load: true,
								callback: function (that) {
									bt.confirm(
										{
											title: 'Delete site backups in bulk',
											msg: 'Do you want to delete selected site backups in batches?',
											icon: 0,
										},
										function (index) {
											layer.close(index);
											that.start_batch({}, function (list) {
												var html = '';
												for (var i = 0; i < list.length; i++) {
													var item = list[i];
													html +=
														'<tr><td><span style="width: 160px;" class="limit-text-length" title="' +
														item.name +
														'">' +
														item.name +
														'</span></td><td class="text-right"><span style="color:' +
														(item.request.status ? '#20a53a' : 'red') +
														'">' +
														item.request.msg +
														'</span></td></tr>';
												}
												backup_table.$batch_success_table({
													title: 'Delete site backups in bulk',
													th: 'file name',
													html: html,
												});
												backup_table.$refresh_table_list(true);
												thatC.$modify_row_data({ backup_count: thatC.event_rows_model.rows.backup_count - list.length });
											});
										}
									);
								},
							}, //分页显示
						},
						{
							type: 'page',
							positon: ['right', 'bottom'], // 默认在右下角
							pageParam: 'p', //分页请求字段,默认为 : p
							page: 1, //当前分页 默认：1
							numberParam: 'limit',
							//分页数量请求字段默认为 : limit
							number: 10,
							//分页数量默认 : 20条
						},
					],
				});
			},
		});
	},
	backup_output_stop: false,
	//实时显示过程
	backup_output_logs: function () {
		var layerT = layer.open({
			type: 1,
			area: '590px',
			title: 'Recovering the backup...',
			closeBtn: 0,
			content: '<div><div><pre class="backup_logs" style="height: 390px;background: #000;color: #fff;margin-bottom: 0;"></pre></div></div>',
		});
		var show_output = setInterval(function () {
			$.post('/files?action=get_progress', function (rdata) {
				if (site.backup_output_stop) {
					layer.close(layerT);
					clearInterval(show_output);
				}
				$('.backup_logs').html(rdata.msg);
				$('.backup_logs').scrollTop($('.backup_logs')[0].scrollHeight);
			});
		}, 1000);
	},
	/**
	 * @description 添加站点
	 */
	add_site: function (callback) {
		var typeId = bt.get_cookie('site_type');
		var add_web = bt_tools.form({
			data: {}, //用于存储初始值和编辑时的赋值内容
			class: '',
			form: [
				{
					label: lan.site.add_site.domain,
					must: '*',
					group: [
						{
							type: 'textarea', //当前表单的类型 支持所有常规表单元素、和复合型的组合表单元素
							name: 'webname', //当前表单的name
							style: { width: '440px', height: '100px', 'line-height': '22px' },
							tips: {
								//使用hover的方式显示提示
								text: lan.site.domain_help,
								style: { top: '15px', left: '15px' },
							},
							keyup: function (value, form, that, config, ev) {
								//键盘事件
								var array = value.webname.split('\n'),
									ress = array[0].split(':')[0],
									oneVal = bt.strim(ress.replace(new RegExp(/([-.])/g), '_')),
									defaultPath = $('#defaultPath').text(),
									is_oneVal = ress.length > 0;
								that.$set_find_value(
									is_oneVal
										? {
												ftp_username: 'ftp_' + oneVal,
												ftp_password: bt.get_random(16),
												datauser: is_oneVal ? 'sql_' + oneVal.substr(0, 16) : '',
												datapassword: bt.get_random(16),
												ps: oneVal,
												path: bt.rtrim(defaultPath, '/') + '/' + ress,
										  }
										: {
												ftp_username: '',
												ftp_password: '',
												datauser: '',
												datapassword: '',
												ps: '',
												path: bt.rtrim(defaultPath, '/'),
										  }
								);
								if (bt.check_domain(ress)) {
									form['redirect'].parents('.block').removeClass('hide');
									if (ress.indexOf('www.') !== 0) {
										form['redirect']
											.next()
											.find('span')
											.text('www.' + ress);
									} else if (ress.indexOf('www.') === 0) {
										form['redirect']
											.next()
											.find('span')
											.text(ress.replace(/^www\./, ''));
									}
								} else {
									form['tourl'].parents('.line').addClass('hide');
									form['redirect'].parents('.block').addClass('hide');
								}
							},
						},
						{
							type: 'checkbox',
							block: true,
							block_class: 'redirect_check',
							hide: true,
							name: 'redirect',
							label_tips: 'Add [<span></span>] domain name to the main domain name',
							event: function (value, form, that, config, ev) {
								var domain = form['redirect'].next().find('span').text(),
									domain_textarea = form['webname'],
									domainList = domain_textarea.val().split('\n'),
									domain_one = domainList[0].split(':')[0];
								if (value['redirect'] == 'on') {
									domain_textarea.val(domain_textarea.val() + '\r' + domain);
									form['tourl'].parents('.line').removeClass('hide');
									var radio_list = form['tourl'].parents('.line').find('.redirect_tourl');
									$('.redirect_tourl:eq(1)')
										.find('label')
										.html('Redirect the main domain name [<span title="' + domain_one + '"> ' + domain_one + '</span>] to [<span title="' + domain + '">' + domain + '</span>] domain name');
									$('.redirect_tourl:eq(2)')
										.find('label')
										.html('Redirect the [<span title="' + domain + '">' + domain + '</span>] domain name to the main domain [<span title="' + domain_one + '">' + domain_one + '</span>]');
								} else {
									for (var i = domainList.length - 1; i >= 0; i--) {
										if (domainList[i] === domain) domainList.splice(i, 1);
									}
									domain_textarea.val(domainList.join('\n'));
									form['tourl'].parents('.line').addClass('hide');
								}
							},
						},
					],
				},
				{
					label: 'Redirect',
					hide: true,
					group: [
						{
							type: 'radio',
							name: 'tourl',
							block: true,
							block_class: 'redirect_tourl',
							label_tips: [
								'No',
								'Redirect the main domain name [<span title=""></span>] to [<span title=""></span>] domain name',
								'Redirect the [<span title=""></span>] domain name to the main domain [<span title=""></span>]',
							],
						},
					],
				},
				{
					label: lan.site.add_site.description,
					group: {
						type: 'text',
						name: 'ps',
						width: '400px',
						placeholder: lan.note_ph, //默认标准备注提示
					},
				},
				{
					label: lan.site.add_site.root,
					must: '*',
					group: {
						type: 'text',
						width: '400px',
						name: 'path',
						icon: {
							type: 'glyphicon-folder-open',
							event: function (ev) {},
						},
						value: '/www/wwwroot',
						placeholder: lan.site.add_site.root_ph,
					},
				},
				{
					label: lan.site.add_site.ftp,
					group: [
						{
							type: 'select',
							name: 'ftp',
							width: '135px',
							disabled: (function () {
								if (bt.config['pure-ftpd']) return !bt.config['pure-ftpd'].setup;
								return true;
							})(),
							list: [
								{ title: lan.site.add_site.dont_create, value: false },
								{ title: lan.site.add_site.create, value: true },
							],
							change: function (value, form, that, config, ev) {
								if (value['ftp'] === 'true') {
									form['ftp_username'].parents('.line').removeClass('hide');
								} else {
									form['ftp_username'].parents('.line').addClass('hide');
								}
							},
						},
						(function () {
							if (bt.config['pure-ftpd']['setup']) return {};
							return {
								type: 'link',
								title: 'FTP is not installed, click Install',
								name: 'installed_ftp',
								event: function (ev) {
									bt.soft.install('pureftpd');
								},
							};
						})(),
					],
				},
				{
					label: lan.site.add_site.ftp_set,
					hide: true,
					group: [
						{
							type: 'text',
							name: 'ftp_username',
							placeholder: lan.site.add_site.ftp_ph,
							width: '175px',
							style: { 'margin-right': '15px' },
						},
						{
							label: lan.site.add_site.password,
							type: 'text',
							placeholder: lan.site.add_site.ftp_password,
							name: 'ftp_password',
							width: '175px',
						},
					],
					help: {
						list: [lan.site.ftp_help],
					},
				},
				{
					label: lan.site.add_site.database,
					group: [
						{
							type: 'select',
							name: 'sql',
							width: '135px',
							disabled: (function () {
								if (bt.config['mysql']) return !bt.config['mysql'].setup;
								return true;
							})(),
							list: [
								{ title: lan.site.add_site.dont_create, value: false },
								{ title: 'MySQL', value: 'MySQL' },
								{
									title: 'SQLServer',
									value: 'SQLServer',
									disabled: true,
									tips: lan.public_backup.unsupport_sqlserver,
								},
							],
							change: function (value, form, that, config, ev) {
								if (value['sql'] === 'MySQL') {
									form['datauser'].parents('.line').removeClass('hide');
									form['codeing'].parents('.bt_select_updown').removeClass('hide');
								} else {
									form['datauser'].parents('.line').addClass('hide');
									form['codeing'].parents('.bt_select_updown').addClass('hide');
								}
							},
						},
						(function () {
							if (bt.config.mysql.setup) return {};
							return {
								type: 'link',
								title: 'Database not installed, click Install',
								name: 'installed_database',
								event: function (ev) {
									bt.soft.install('mysql');
								},
							};
						})(),
						{
							type: 'select',
							name: 'codeing',
							hide: true,
							width: '135px',
							list: [
								{ title: 'utf8', value: 'utf8' },
								{ title: 'utf8mb4', value: 'utf8mb4' },
								{ title: 'gbk', value: 'gbk' },
								{ title: 'big5', value: 'big5' },
							],
						},
					],
				},
				{
					label: lan.site.add_site.database_set,
					hide: true,
					group: [
						{
							type: 'text',
							name: 'datauser',
							placeholder: lan.site.add_site.database_ph,
							width: '175px',
							style: { 'margin-right': '15px' },
						},
						{
							label: lan.site.add_site.password,
							type: 'text',
							placeholder: lan.site.add_site.database_password,
							name: 'datapassword',
							width: '175px',
						},
					],
					help: {
						class: '',
						style: '',
						list: [lan.site.database_help],
					},
				},
				{
					label: lan.site.add_site.php_version,
					group: [
						{
							type: 'select',
							name: 'version',
							width: '135px',
							list: {
								url: '/site?action=GetPHPVersion',
								dataFilter: function (res) {
									var arry = [];
									for (var i = res.length - 1; i >= 0; i--) {
										var item = res[i];
										arry.push({ title: item.name, value: item.version });
									}
									return arry;
								},
							},
						},
					],
				},
				{
					label: lan.site.add_site.category,
					group: [
						{
							type: 'select',
							name: 'type_id',
							width: '135px',
							list: {
								url: '/site?action=get_site_types',
								dataFilter: function (res) {
									var arry = [];
									$.each(res, function (index, item) {
										arry.push({ title: item.name, value: item.id });
									});
									return arry;
								},
								success: function (res, formObj) {
									setTimeout(function () {
										var index = -1;
										for (var i = 0; i < res.length; i++) {
											if (res[i].id == typeId) {
												index = i;
												break;
											}
										}
										if (index != -1) formObj.element.find('.bt_select_updown[data-name="type_id"]').find('.bt_select_list li').eq(index).click();
									}, 100);
								},
							},
						},
					],
				},
				{
					label: 'SSL',
					class: 'ssl_checkbox',
					help: {
						style: 'color: red;line-height: 17px;margin-top: 8px;',
						list: ['If you need to apply for SSL, please make sure that the domain name has added A record resolution for the domain name'],
					},
					group: [
						{
							type: 'checkbox',
							name: 'set_ssl',
							title: 'Apply for SSL',
							class: 'site_ssl_check',
							style: { 'margin-right': '10px', 'margin-left': '0' },
						},
						{
							type: 'checkbox',
							name: 'force_ssl',
							class: 'site_ssl_check',
							title: 'HTTP redirect to HTTPS',
							event: function (value, form, that, config, ev) {
								var force_ssl = $(this).is(':checked');
								if (force_ssl) {
									$('.site_ssl_check:eq(0)').find('i').addClass('active');
									$('input[name=set_ssl]').prop('checked', force_ssl);
								}
							},
						},
					],
				},
			],
		});
		var bath_web = bt_tools.form({
			class: 'plr10',
			form: [
				{
					line_style: { position: 'relative' },
					group: {
						type: 'textarea', //当前表单的类型 支持所有常规表单元素、和复合型的组合表单元素
						name: 'bath_code', //当前表单的name
						style: { width: '560px', height: '180px', 'line-height': '22px', 'font-size': '13px' },
						value: lan.site.add_site.bath_code_ph,
					},
				},
				{
					group: {
						type: 'help',
						style: { 'margin-top': '0' },
						class: 'none-list-style',
						list: [
							lan.site.add_site.bath_tips1,
							lan.site.add_site.bath_tips2,
							lan.site.add_site.bath_tips3,
							lan.site.add_site.bath_tips4,
							lan.site.add_site.bath_tips5,
							lan.site.add_site.bath_tips6,
							lan.site.add_site.bath_tips7,
							lan.site.add_site.bath_tips8,
						],
					},
				},
			],
		});
		var deploy_wp = bt_tools.form({
			form: [
				{
					label: 'Domain',
					group: {
						type: 'text',
						name: 'domain',
						width: '400px',
						placeholder: 'Your website domain name',
					},
				},
				{
					label: 'Website Title',
					group: {
						type: 'text',
						name: 'weblog_title',
						width: '400px',
						placeholder: 'Website title for wordpress',
					},
				},
				{
					label: 'Language',
					group: [
						{
							type: 'select',
							name: 'language',
							width: '230px',
							list: {
								url: '/site?action=get_language',
								dataFilter: function (rlist) {
									var lan = [];
									$.each(rlist.msg, function (index, item) {
										lan.push({ title: item, value: index });
									});
									return lan;
								},
							},
						},
					],
				},
				{
					label: 'PHP version',
					group: [
						{
							type: 'select',
							name: 'php_version',
							width: '230px',
							list: add_web['config']['form'][8]['group'][0]['list'],
						},
					],
				},
				{
					label: 'User name',
					group: {
						type: 'text',
						name: 'user_name',
						width: '400px',
						placeholder: 'WordPress backend user',
					},
				},
				{
					label: 'Password',
					group: [
						{
							type: 'text',
							name: 'admin_password',
							placeholder: 'WordPress backend password',
							width: '230px',
							style: { 'margin-right': '15px' },
						},
						{
							type: 'checkbox',
							name: 'pw_weak',
							title: 'Allow weak passwords',
						},
					],
				},
				{
					label: 'Email',
					group: {
						type: 'text',
						name: 'admin_email',
						width: '400px',
						placeholder: 'Your email address',
					},
				},
				{
					label: 'Prefix',
					group: {
						type: 'text',
						name: 'prefix',
						width: '400px',
						value: 'wp_',
						placeholder: 'Wordpress table name prefix',
					},
				},
				{
					label: 'Enable cache',
					style: { 'min-height': '0', 'line-height': '15px', 'margin-bottom': ' 0' },
					group: [
						{
							type: 'checkbox',
							name: 'enable_cache',
							title: 'Enable caching, currently only supports nginx',
						},
					],
				},
			],
		});

		var web_tab = bt_tools.tab({
			class: 'pd20',
			type: 0,
			theme: { nav: 'mlr20' },
			active: 1, //激活TAB下标
			list: [
				{
					title: lan.site.add_site.create_site,
					name: 'createSite',
					content: add_web.$reader_content(),
					success: function () {
						add_web.$event_bind();
					},
				},
				{
					title: lan.site.add_site.batch_creat,
					name: 'batchCreation',
					content: bath_web.$reader_content(),
					success: function () {
						bath_web.$event_bind();
					},
				},
				{
					title: 'Wordpress deploy',
					name: 'wordpressDeploy',
					content: '',
					success: function (el) {
						el.html(deploy_wp.$reader_content());
						deploy_wp.$event_bind();
						$(el).find('form .line:last-child .tname').css({ height: '22px', 'line-height': '22px' });
					},
				},
			],
		});
		bt_tools.open({
			title: lan.site.add_site.add_site_title,
			skin: 'custom_layer',
			btn: [lan.public.submit, lan.site.no],
			content: web_tab.$reader_content(),
			success: function ($layer) {
				web_tab.$init();

				$layer.find('.tab-con').scroll(function () {
					$layer.find('.bt_select_list').removeClass('show');
				});
				// $layer.find('.layui-layer-content, .tab-con').css('overflow', $(window).height() > $layer.height() ? 'visible' : 'auto');
			},
			yes: function (indexs) {
				var tabContent = add_web,
					tabActive = web_tab.active;
				switch (tabActive) {
					case 1:
						tabContent = bath_web;
						break;
					case 2:
						tabContent = deploy_wp;
						break;
				}
				var formValue = tabContent.$get_form_value();
				if (tabActive != 2 && formValue.webname === '') {
					bt.msg({ status: false, msg: '网站域名不能为空！' });
					return false;
				}

				if (tabActive == 0) {
					// 创建站点
					var loading = bt.load();
					add_web.$get_form_element(true);
					if (formValue.webname === '') {
						add_web.form_element.webname.focus();
						bt_tools.msg(lan.public.domain_format_not_right, 2);
						return;
					}
					var webname = bt.replace_all(formValue.webname, 'http[s]?:\\/\\/', ''),
						web_list = webname.split('\n'),
						param = { webname: { domain: '', domainlist: [], count: 0 }, type: 'PHP', port: 80 },
						arry = ['ps', ['path', lan.site.site_menu_2], 'type_id', 'version', 'ftp', 'sql', 'ftp_username', 'ftp_password', 'datauser', 'datapassword', 'codeing'];
					for (var i = 0; i < web_list.length; i++) {
						var temps = web_list[i].replace(/\r\n/, '').split(':');
						if (i === 0) {
							param['webname']['domain'] = web_list[i];
							if (typeof temps[1] != 'undefined') param['port'] = temps[1];
						} else {
							param['webname']['domainlist'].push(web_list[i]);
						}
					}
					param['webname']['count'] = param['webname']['domainlist'].length;
					param['webname'] = JSON.stringify(param['webname']);
					$.each(arry, function (index, item) {
						if (formValue[item] == '' && Array.isArray(item)) {
							bt_tools.msg(item[1] + lan.site.add_site.empty_ps, 2);
							return false;
						}
						Array.isArray(item) ? (item = item[0]) : '';
						if (formValue['ftp'] === 'false' && (item === 'ftp_username' || item === 'ftp_password')) return true;
						if (formValue['sql'] === 'false' && (item === 'datauser' || item === 'datapassword')) return true;
						param[item] = formValue[item];
					});
					param['set_ssl'] = $('input[name=set_ssl]').prop('checked') ? 1 : 0;
					param['force_ssl'] = $('input[name=force_ssl]').prop('checked') ? 1 : 0;
					var is_redirect = $('.redirect_check').hasClass('hide');
					if (!is_redirect) {
						var redirect_check = $('.redirect_check input[name=redirect]').is(':checked');
						if (redirect_check) {
							var domains = $('.redirect_tourl input[name=tourl]:checked').next().find('span');
							if (domains.length != 0) {
								param.redirect = $(domains[0]).text();
								param.tourl = $(domains[1]).text();
							}
						}
					}
					bt.send('AddSite', 'site/AddSite', param, function (rdata) {
						loading.close();
						if (rdata.siteStatus) {
							layer.close(indexs);
							if (callback) callback(rdata, param);
							var html = '',
								ftpData = '',
								sqlData = '';
							if (rdata.ftpStatus) {
								var list = [];
								list.push({ title: lan.site.user, val: rdata.ftpUser });
								list.push({ title: lan.site.password, val: rdata.ftpPass });
								var item = {};
								item.title = lan.site.ftp;
								item.list = list;
								ftpData = bt.render_ps(item);
							}
							if (rdata.databaseStatus) {
								var list = [];
								list.push({ title: lan.site.database_name, val: rdata.databaseUser });
								list.push({ title: lan.site.user, val: rdata.databaseUser });
								list.push({ title: lan.site.password, val: rdata.databasePass });
								var item = {};
								item.title = lan.site.database_txt;
								item.list = list;
								sqlData = bt.render_ps(item);
							}
							if (ftpData == '' && sqlData == '') {
								bt.msg({ msg: lan.site.success_txt, icon: 1 });
							} else {
								bt.open({
									type: 1,
									area: '600px',
									title: lan.site.success_txt,
									closeBtn: 2,
									shadeClose: false,
									content: "<div class='success-msg'><div class='pic'><img src='/static/img/success-pic.png'></div><div class='suc-con'>" + ftpData + sqlData + '</div></div>',
								});

								if ($('.success-msg').height() < 150) {
									$('.success-msg').find('img').css({ width: '150px', 'margin-top': '30px' });
								}
							}
						} else {
							bt.msg(rdata);
						}
					});
				} else if (tabActive == 1) {
					//批量创建
					var loading = bt.load();
					if (formValue.bath_code === '') {
						bt_tools.msg(lan.site.add_site.batch_site_ps, 2);
						return false;
					} else {
						var arry = formValue.bath_code.split('\n'),
							config = '',
							_list = [];
						for (var i = 0; i < arry.length; i++) {
							var item = arry[i],
								params = item.split('|'),
								_arry = [];
							if (item === '') continue;
							for (var j = 0; j < params.length; j++) {
								var line = i + 1,
									items = bt.strim(params[j]);
								_arry.push(items);
								switch (j) {
									case 0: //参数一:域名
										var domainList = items.split(',');
										for (var z = 0; z < domainList.length; z++) {
											var domain_info = domainList[z],
												_domain = domain_info.split(':');
											if (!bt.check_domain(_domain[0])) {
												bt_tools.msg(lan.site.add_site.error_line + line + lan.site.add_site.domain_error + '【' + domain_info + '】', 2);
												return false;
											}
											if (typeof _domain[1] !== 'undefined') {
												if (!bt.check_port(_domain[1])) {
													bt_tools.msg(lan.site.add_site.error_line + line + lan.site.add_site.port_error + '【' + _domain[1] + '】', 2);
													return false;
												}
											}
										}
										break;
									case 1: //参数二:站点目录
										if (items !== '1') {
											if (items.indexOf('/') < -1) {
												bt_tools.msg(lan.site.add_site.error_line + line + lan.site.add_site.port_error + '【' + items + '】', 2);
												return false;
											}
										}
										break;
								}
							}
							_list.push(_arry.join('|').replace(/\r|\n/, ''));
						}
					}
					bt.send(
						'create_type',
						'site/create_website_multiple',
						{
							create_type: 'txt',
							websites_content: JSON.stringify(_list),
						},
						function (rdata) {
							loading.close();
							if (rdata.status) {
								var _html = '';
								layer.close(indexs);
								if (callback) callback(rdata);
								$.each(rdata.error, function (key, item) {
									_html += '<tr><td>' + key + '</td><td>--</td><td>--</td><td style="text-align: right;"><span style="color:red">' + item + '</td></td></tr>';
								});
								$.each(rdata.success, function (key, item) {
									_html +=
										'<tr><td>' +
										key +
										'</td><td>' +
										(item.ftp_status ? '<span style="color:#20a53a">' + lan.site.add_site.success + '</span>' : '<span>' + lan.site.add_site.not_created + '</span>') +
										'</td><td>' +
										(item.db_status ? '<span style="color:#20a53a">' + lan.site.add_site.success + '</span>' : '<span>' + lan.site.add_site.not_created + '</span>') +
										'</td><td  style="text-align: right;"><span style="color:#20a53a">' +
										lan.site.add_site.created +
										'</span></td></tr>';
								});
								bt.open({
									type: 1,
									title: lan.site.add_site.batch_add_site,
									area: ['500px', '450px'],
									shadeClose: false,
									closeBtn: 2,
									content:
										'<div class="fiexd_thead divtable" style="margin: 15px 30px 15px 30px;overflow: auto;height: 360px;"><table class="table table-hover"><thead><tr><th>' +
										lan.site.add_site.site_name +
										'</th><th>FTP</th><th>' +
										lan.site.add_site.database +
										'</th><th style="text-align:right;width:150px;">' +
										lan.site.add_site.opt_result +
										'</th></tr></thead><tbody>' +
										_html +
										'</tbody></table></div>',
									success: function () {
										$('.fiexd_thead').scroll(function () {
											var scrollTop = this.scrollTop;
											this.querySelector('thead').style.transform = 'translateY(' + scrollTop + 'px)';
										});
									},
								});
							} else {
								bt.msg(rdata);
							}
						}
					);
				} else {
					//wp一键部署
					var param = { webname: { domain: '', domainlist: [], count: 0 }, type: 'PHP', port: 80, type_id: 0, ftp: false, sql: 'MySQL', codeing: 'utf8', set_ssl: 0, force_ssl: 0, project_type: 'WP' };
					if (formValue.domain == '') return layer.msg('Wordpress domain name cannot be empty', { icon: 2 });
					if (formValue.weblog_title == '') return layer.msg('Wordpress site title cannot be empty', { icon: 2 });
					if (formValue.user_name == '') return layer.msg('Wordpress backend user cannot be empty', { icon: 2 });
					if (formValue.admin_password == '') return layer.msg('Wordpress backend password cannot be empty', { icon: 2 });
					if (formValue.admin_email == '') return layer.msg('Email address cannot be empty', { icon: 2 });
					if (formValue.prefix == '') return layer.msg('Wordpress table name prefix cannot be empty', { icon: 2 });

					var _domain = bt.strim(formValue.domain.replace(new RegExp(/([-.])/g), '_'));
					param['webname']['domain'] = formValue.domain;
					param['webname'] = JSON.stringify(param['webname']);

					param['path'] = '/www/wwwroot/' + formValue.domain;
					param['ps'] = _domain;
					param['version'] = formValue.php_version;
					param['datauser'] = 'sql_' + _domain;
					param['datapassword'] = bt.get_random(16);

					// 密码强度判断
					param['password'] = formValue['admin_password'];
					param['pw_weak'] = formValue['pw_weak'] ? 'on' : 'off';
					param['email'] = formValue['admin_email'];

					var loading = bt.load('Creating website, please wait...');
					// 1.通过主域名生成域名文件地址等信息
					bt.send('AddSite', 'site/AddSite', param, function (rdata) {
						loading.close();
						if (typeof rdata.status === 'boolean' && !rdata.status) return layer.msg(rdata.msg, { icon: 2, time: 0, shade: 0.3, shadeClose: true });
						// 2.通过回调的siteId,d_id部署wp
						if (rdata.databaseStatus) {
							formValue['d_id'] = rdata.d_id;
							formValue['s_id'] = rdata.siteId;
							formValue['enable_cache'] = formValue['enable_cache'] ? 1 : 0;
							formValue['pw_weak'] = formValue['pw_weak'] ? 'on' : 'off';

							var loadingWp = bt.load('Deploying wordpress, please wait...');
							bt.send('deploy_wp', 'site/deploy_wp', formValue, function (deploy) {
								loadingWp.close();
								if (deploy.status) {
									layer.close(indexs);
									if (callback) callback(deploy);
								}
								layer.msg(deploy.msg, { icon: deploy.status ? 1 : 2 });
							});
						}
					});
				}
			},
		});
	},
	set_default_page: function () {
		bt.open({
			type: 1,
			area: '460px',
			title: lan.site.change_defalut_page,
			closeBtn: 2,
			shift: 0,
			content:
				'<div class="change-default pd20"><button  class="btn btn-default btn-sm ">' +
				lan.site.default_doc +
				'</button><button  class="btn btn-default btn-sm">' +
				lan.site.err_404 +
				'</button>	<button  class="btn btn-default btn-sm ">' +
				lan.site.empty_page +
				'</button><button  class="btn btn-default btn-sm ">' +
				lan.site.default_page_stop +
				'</button></div>',
		});
		setTimeout(function () {
			$('.change-default button').click(function () {
				bt.site.get_default_path($(this).index(), function (path) {
					bt.pub.on_edit_file(0, path);
				});
			});
		}, 100);
	},
	set_default_site: function () {
		bt.site.get_default_site(function (rdata) {
			var arrs = [];
			arrs.push({ title: lan.site.default_site_not_set, value: '0' });
			for (var i = 0; i < rdata.sites.length; i++)
				arrs.push({
					title: rdata.sites[i].name,
					value: rdata.sites[i].name,
				});
			var form = {
				title: lan.site.default_site_yes,
				area: '530px',
				list: [
					{
						title: lan.site.default_site,
						name: 'defaultSite',
						width: '300px',
						value: rdata.defaultSite,
						type: 'select',
						items: arrs,
					},
				],
				btns: [
					bt.form.btn.close(),
					bt.form.btn.submit(lan.site.submit, function (rdata, load) {
						bt.site.set_default_site(rdata.defaultSite, function (rdata) {
							load.close();
							bt.msg(rdata);
						});
					}),
				],
			};
			bt.render_form(form);
			$('.line').after($(bt.render_help([lan.site.default_site_help_1, lan.site.default_site_help_2])).addClass('plr20'));
		});
	},
	//PHP-CLI
	get_cli_version: function () {
		$.post('/config?action=get_cli_php_version', {}, function (rdata) {
			if (rdata.status === false) {
				layer.msg(rdata.msg, { icon: 2 });
				return;
			}
			var _options = '';
			for (var i = rdata.versions.length - 1; i >= 0; i--) {
				var ed = '';
				if (rdata.select.version == rdata.versions[i].version) ed = 'selected';
				_options += '<option value="' + rdata.versions[i].version + '" ' + ed + '>' + rdata.versions[i].name + '</option>';
			}
			var body =
				'<div class="bt-form bt-form pd20 pb70">\
              <div class="line">\
                  <span class="tname">' +
				lan.site.php_cli_ver +
				'</span>\
                  <div class="info-r ">\
                      <select class="bt-input-text mr5" name="php_version" style="width:300px">' +
				_options +
				'</select>\
                  </div>\
              </div >\
              <ul class="help-info-text c7 plr20">\
                  <li>' +
				lan.site.php_cli_tips1 +
				'</li>\
                  <li>' +
				lan.site.php_cli_tips2 +
				'</li>\
              </ul>\
              <div class="bt-form-submit-btn"><button type="button" class="btn btn-sm btn-danger" onclick="layer.closeAll()">' +
				lan.site.turn_off +
				'</button><button type="button" class="btn btn-sm btn-success" onclick="site.set_cli_version()">' +
				lan.site.submit +
				'</button></div></div>';

			layer.open({
				type: 1,
				title: lan.site.set_php_cli_cmd,
				area: '560px',
				closeBtn: 2,
				shadeClose: false,
				content: body,
			});
		});
	},
	set_cli_version: function () {
		var php_version = $("select[name='php_version']").val();
		var loading = bt.load();
		$.post('/config?action=set_cli_php_version', { php_version: php_version }, function (rdata) {
			loading.close();
			if (rdata.status) {
				layer.closeAll();
			}
			layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
		});
	},
	del_site: function (wid, wname, callback) {
		var num1 = bt.get_random_num(1, 9),
			num2 = bt.get_random_num(1, 9),
			title = '';
		title = typeof wname === 'function' ? 'Deleting sites in batches' : lan.site.site_del_title + ' [ ' + wname + ' ]';
		layer.open({
			type: 1,
			title: title,
			icon: 0,
			skin: 'delete_site_layer',
			area: '480px',
			closeBtn: 2,
			shadeClose: true,
			content:
				'\
              <div class="bt-form webDelete pd30" id="site_delete_form">\
                  <i class="layui-layer-ico layui-layer-ico0"></i>\
                  <div class="f13 check_title">' +
				lan.site.site_del_info +
				'</div>\
                  <div class="check_type_group">\
                      <label>\
                          <input type="checkbox" name="ftp" />\
                          <span>FTP</span>\
                      </label>\
                      <label>\
                          <input type="checkbox" name="database">\
                          <span>' +
				lan.site.database +
				'</span>\
                          ' +
				(!recycle_bin_db_open ? '<span class="glyphicon glyphicon-info-sign" style="color: red"></span>' : '') +
				'\
                      </label>\
                      <label style="margin-right: 0;">\
                          <input type="checkbox" name="path">\
                          <span>' +
				lan.site.root_dir +
				'</span>\
                          ' +
				(!recycle_bin_open ? '<span class="glyphicon glyphicon-info-sign" style="color: red"></span>' : '') +
				'\
                      </label>\
                  </div>\
                  <div class="vcode">\
                      ' +
				lan.bt.cal_msg +
				'<span class="text">' +
				num1 +
				' + ' +
				num2 +
				'</span>=\
                      <input type="number" id="vcodeResult" value="" />\
                  </div>\
              </div>\
          ',
			btn: [lan.public.ok, lan.public.cancel],
			success: function (layers, indexs) {
				$(layers)
					.find('.check_type_group label')
					.hover(
						function () {
							var name = $(this).find('input').attr('name');
							if (name === 'data' && !recycle_bin_db_open) {
								layer.tips('Risky operation: the current database recycle bin is not open, delete the database will disappear forever!', this, {
									tips: [1, 'red'],
									time: 0,
								});
							} else if (name === 'path' && !recycle_bin_open) {
								layer.tips('Risky operation: The current file recycle bin is not open, delete the site directory will disappear forever!', this, {
									tips: [1, 'red'],
									time: 0,
								});
							}
						},
						function () {
							layer.closeAll('tips');
						}
					);
			},
			yes: function (indexs) {
				var vcodeResult = $('#vcodeResult'),
					data = { id: wid, webname: wname };
				$('#site_delete_form input[type=checkbox]').each(function (index, item) {
					if ($(item).is(':checked')) data[$(item).attr('name')] = 1;
				});
				if (vcodeResult.val() === '') {
					layer.tips('The result cannot be null', vcodeResult, { tips: [1, 'red'], time: 3000 });
					vcodeResult.focus();
					return false;
				} else if (parseInt(vcodeResult.val()) !== num1 + num2) {
					layer.tips('The calculation is incorrect', vcodeResult, { tips: [1, 'red'], time: 3000 });
					vcodeResult.focus();
					return false;
				}
				var is_database = data.hasOwnProperty('database'),
					is_path = data.hasOwnProperty('path'),
					is_ftp = data.hasOwnProperty('ftp');
				if (!is_database && !is_path && (!is_ftp || is_ftp)) {
					if (typeof wname === 'function') {
						wname(data);
						return false;
					}
					bt.site.del_site(data, function (rdata) {
						layer.close(indexs);
						if (callback) callback(rdata);
						bt.msg(rdata);
					});
					return false;
				}
				if (typeof wname === 'function') {
					delete data.id;
					delete data.webname;
				}
				layer.close(indexs);
				var ids = JSON.stringify(wid instanceof Array ? wid : [wid]),
					countDown = typeof wname === 'string' ? 4 : 9;
				title = typeof wname === 'function' ? 'Verify the information twice and delete sites in batches' : 'Verify information twice, delete site [ ' + wname + ' ]';
				var loadT = bt.load('Checking site data information, please wait...');
				bt.send('check_del_data', 'site/check_del_data', { ids: ids }, function (res) {
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
							'<div class="check_layer_title">Please calm down for a few seconds and confirm the following data to be deleted.</div>' +
							'<div class="check_layer_content">' +
							'<div class="check_layer_item">' +
							'<div class="check_layer_site"></div>' +
							'<div class="check_layer_database"></div>' +
							'</div>' +
							'</div>' +
							'<div class="check_layer_error ' +
							(data.database && recycle_bin_db_open ? 'hide' : '') +
							'"><span class="glyphicon glyphicon-info-sign"></span>Risks: The database recycle bin function is not enabled at present. After the database is deleted, the database will disappear forever!</div>' +
							'<div class="check_layer_error ' +
							(data.path && recycle_bin_open ? 'hide' : '') +
							'"><span class="glyphicon glyphicon-info-sign"></span>Risk: The file recycle bin function is disabled at present. After a site directory is deleted, the site directory will disappear forever!</div>' +
							'<div class="check_layer_message">Please read the above information to be deleted carefully to prevent site data from being deleted by mistake. Confirm that there are still <span style="color:red;font-weight: bold;">' +
							countDown +
							'</span> seconds left to delete.</div>' +
							'</div>',
						btn: ['Confirm deletion (continue operation after ' + countDown + 'seconds)', 'Cancel'],
						success: function (layers) {
							var html = '',
								rdata = res.data;
							for (var i = 0; i < rdata.length; i++) {
								var item = rdata[i],
									newTime = parseInt(new Date().getTime() / 1000),
									t_icon = '<span class="glyphicon glyphicon-info-sign" style="color: red;width:15px;height: 15px;;vertical-align: middle;"></span>';

								(site_html = (function (item) {
									if (!is_path) return '';
									var is_time_rule = newTime - item.st_time > 86400 * 30 && item.total > 1024 * 10,
										is_path_rule = res.file_size <= item.total,
										dir_time = bt.format_data(item.st_time, 'yyyy-MM-dd'),
										dir_size = bt.format_size(item.total);

									var f_html =
										'<i ' + (is_path_rule ? 'class="warning"' : '') + ' style = "vertical-align: middle;" > ' + (item.limit ? 'More than 50 MB' : dir_size) + '</i> ' + (is_path_rule ? t_icon : '');
									var f_title =
										(is_path_rule ? 'Note: This directory may contain important data. Exercise caution when performing this operation.\n' : '') +
										'directory：' +
										item.path +
										'(' +
										(item.limit ? 'greater than ' : '') +
										dir_size +
										')';

									return (
										'<div class="check_layer_site">' +
										'<span title="site：' +
										item.name +
										'">Site: ' +
										item.name +
										'</span>' +
										'<span title="' +
										f_title +
										'" >Path: <span style="vertical-align: middle;max-width: 160px;width: auto;">' +
										item.path +
										'</span> (' +
										f_html +
										')</span>' +
										'<span title="' +
										(is_time_rule ? 'Note: This site is created earlier and may contain important data. Exercise caution when performing this operation.\n' : '') +
										'time：' +
										dir_time +
										'">Create: <i ' +
										(is_time_rule ? 'class="warning"' : '') +
										'>' +
										dir_time +
										'</i></span>' +
										'</div>'
									);
								})(item)),
									(database_html = (function (item) {
										if (!is_database || !item.database) return '';
										var is_time_rule = newTime - item.st_time > 86400 * 30 && item.total > 1024 * 10,
											is_database_rule = res.db_size <= item.database.total,
											database_time = bt.format_data(item.database.st_time, 'yyyy-MM-dd'),
											database_size = bt.format_size(item.database.total);

										var f_size = '<i ' + (is_database_rule ? 'class="warning"' : '') + ' style = "vertical-align: middle;" > ' + database_size + '</i> ' + (is_database_rule ? t_icon : '');
										var t_size = 'Note: This database is large and may contain important data. Exercise caution when performing this operation.\ndatabase：' + database_size;

										return (
											'<div class="check_layer_database">' +
											'<span title="database：' +
											item.database.name +
											'">DB: ' +
											item.database.name +
											'</span>' +
											'<span title="' +
											t_size +
											'">Size: ' +
											f_size +
											'</span>' +
											'<span title="' +
											(is_time_rule && item.database.total != 0 ? 'important：This database is created earlier and may contain important data. Exercise caution when performing this operation.' : '') +
											'time：' +
											database_time +
											'">Create: <i ' +
											(is_time_rule && item.database.total != 0 ? 'class="warning"' : '') +
											'>' +
											database_time +
											'</i></span>' +
											'</div>'
										);
									})(item));
								if (site_html + database_html !== '') html += '<div class="check_layer_item">' + site_html + database_html + '</div>';
							}
							if (html === '') html = '<div style="text-align: center;width: 100%;height: 100%;line-height: 300px;font-size: 15px;">No data</div>';
							$('.check_layer_content').html(html);
							var interVal = setInterval(function () {
								countDown--;
								$(layers)
									.find('.layui-layer-btn0')
									.text('Confirm deletion (continue operation after ' + countDown + ' seconds)');
								$(layers).find('.check_layer_message span').text(countDown);
							}, 1000);
							setTimeout(function () {
								$(layers).find('.layui-layer-btn0').text('Confirm the deletion');
								$(layers).find('.check_layer_message').html('<span style="color:red">Note: please read the above information carefully to prevent site data from being deleted by mistake</span>');
								$(layers).removeClass('active');
								clearInterval(interVal);
							}, countDown * 1000);
						},
						yes: function (indes, layers) {
							if ($(layers).hasClass('active')) {
								layer.tips('Please confirm the information and try again later. ' + countDown + ' seconds left', $(layers).find('.layui-layer-btn0'), {
									tips: [1, 'red'],
									time: 3000,
								});
								return;
							}
							if (typeof wname === 'function') {
								wname(data);
							} else {
								bt.site.del_site(data, function (rdata) {
									layer.closeAll();
									if (rdata.status) site.get_list();
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
	batch_site: function (type, obj, result) {
		if (obj == undefined) {
			obj = {};
			var arr = [];
			result = { count: 0, error_list: [] };
			$('input[type="checkbox"].check:checked').each(function () {
				var _val = $(this).val();
				if (!isNaN(_val)) arr.push($(this).parents('tr').data('item'));
			});
			if (type == 'site_type') {
				bt.site.get_type(function (tdata) {
					var types = [];
					for (var i = 0; i < tdata.length; i++) types.push({ title: tdata[i].name, value: tdata[i].id });
					var form = {
						title: lan.site.set_site_classification,
						area: '530px',
						list: [
							{
								title: lan.site.default_site,
								name: 'type_id',
								width: '300px',
								type: 'select',
								items: types,
							},
						],
						btns: [
							bt.form.btn.close(),
							bt.form.btn.submit(lan.site.submit, function (rdata, load) {
								var ids = [];
								for (var x = 0; x < arr.length; x++) ids.push(arr[x].id);
								bt.site.set_site_type(
									{
										id: rdata.type_id,
										site_array: JSON.stringify(ids),
									},
									function (rrdata) {
										if (rrdata.status) {
											load.close();
											site.get_list();
										}
										bt.msg(rrdata);
									}
								);
							}),
						],
					};
					bt.render_form(form);
				});
				return;
			}
			var thtml = "<div class='options'><label style=\"width:100%;\"><input type='checkbox' id='delpath' name='path'><span>" + lan.site.all_del_info + '</span></label></div>';
			bt.show_confirm(
				lan.site.all_del_site,
				"<a style='color:red;'>" + lan.get('del_all_site', [arr.length]) + '</a>',
				function () {
					if ($('#delpath').is(':checked')) obj.path = '1';
					obj.data = arr;
					bt.closeAll();
					site.batch_site(type, obj, result);
				},
				thtml
			);

			return;
		}
		var item = obj.data[0];
		switch (type) {
			case 'del':
				if (obj.data.length < 1) {
					site.get_list();
					bt.msg({ msg: lan.get('del_all_site_ok', [result.count]), icon: 1, time: 5000 });
					return;
				}
				var data = { id: item.id, webname: item.name, path: obj.path };
				bt.site.del_site(data, function (rdata) {
					if (rdata.status) {
						result.count += 1;
					} else {
						result.error_list.push({ name: item.item, err_msg: rdata.msg });
					}
					obj.data.splice(0, 1);
					site.batch_site(type, obj, result);
				});
				break;
		}
	},
	set_class_type: function () {
		var _form_data = bt.render_form_line({
			title: '',
			items: [
				{ placeholder: lan.site.input_classification_name, name: 'type_name', width: '50%', type: 'text' },
				{
					name: 'btn_submit',
					text: lan.site.add,
					type: 'button',
					callback: function (sdata) {
						bt.site.add_type(sdata.type_name, function (ldata) {
							if (ldata.status) {
								$('[name="type_name"]').val('');
								site.get_class_type();
								site.init_site_type();
							}
							bt.msg(ldata);
						});
					},
				},
			],
		});
		bt.open({
			type: 1,
			area: '350px',
			title: lan.site.mam_site_classificacion,
			closeBtn: 2,
			shift: 5,
			shadeClose: true,
			content:
				"<div class='bt-form edit_site_type'><div class='divtable mtb15' style='overflow:auto'>" +
				_form_data.html +
				"<table id='type_table' class='table table-hover' width='100%'></table></div></div>",
			success: function () {
				bt.render_clicks(_form_data.clicks);
				site.get_class_type(function (res) {
					$('#type_table').on('click', '.del_type', function () {
						var _this = $(this);
						var item = _this.parents('tr').data('item');
						if (item.id == 0) {
							bt.msg({ icon: 2, msg: lan.site.default_classification_cant_operation });
							return;
						}
						bt.confirm(
							{
								msg: lan.site.sure_del_classification,
								title: lan.site.del_classification + '【' + item.name + '】',
							},
							function () {
								bt.site.del_type(item.id, function (ret) {
									if (ret.status) {
										site.get_class_type();
										site.init_site_type();
										bt.set_cookie('site_type', '-1');
									}
									bt.msg(ret);
								});
							}
						);
					});
					$('#type_table').on('click', '.edit_type', function () {
						var item = $(this).parents('tr').data('item');
						if (item.id == 0) {
							bt.msg({ icon: 2, msg: lan.site.default_classification_cant_operation });
							return;
						}
						bt.render_form({
							title: lan.site.edit_classification_mam + '【' + item.name + '】',
							area: '350px',
							list: [
								{
									title: lan.site.classification_name,
									width: '150px',
									name: 'name',
									value: item.name,
								},
							],
							btns: [
								{ title: lan.site.turn_off, name: 'close' },
								{
									title: lan.site.submit,
									name: 'submit',
									css: 'btn-success',
									callback: function (rdata, load, callback) {
										bt.site.edit_type({ id: item.id, name: rdata.name }, function (edata) {
											if (edata.status) {
												load.close();
												site.get_class_type();
												site.init_site_type();
											}
											bt.msg(edata);
										});
									},
								},
							],
						});
					});
				});
			},
		});
	},
	get_class_type: function (callback) {
		site.get_types(function (rdata) {
			bt.render({
				table: '#type_table',
				columns: [
					{ field: 'name', title: lan.site.name },
					{
						field: 'opt',
						width: '80px',
						title: lan.site.operate,
						templet: function (item) {
							return '<a class="btlink edit_type" href="javascript:;">' + lan.site.edit + '</a> | <a class="btlink del_type" href="javascript:;">' + lan.site.del + '</a>';
						},
					},
				],
				data: rdata,
			});
			$('.layui-layer-page').css({
				'margin-top': '-' + $('.layui-layer-page').height() / 2 + 'px',
				top: '50%',
			});
			if (callback) callback(rdata);
		});
	},
	ssl: {
		my_ssl_msg: null,

		//续签订单内
		renew_ssl: function (siteName, auth_type, index) {
			acme.siteName = siteName;
			if (index.length === 32 && index.indexOf('/') === -1) {
				acme.renew(index, function (rdata) {
					site.ssl.ssl_result(rdata, auth_type, siteName);
				});
			} else {
				acme.get_cert_init(index, siteName, function (cert_init) {
					acme.domains = cert_init.dns;
					var options = '<option value="http">File verification - HTTP</option>';
					for (var i = 0; i < cert_init.dnsapi.length; i++) {
						options += '<option value="' + cert_init.dnsapi[i].name + '">DNS verification - ' + cert_init.dnsapi[i].title + '</option>';
					}
					acme.select_loadT = layer.open({
						title: "Renew Let's Encrypt Certificate",
						type: 1,
						closeBtn: 2,
						shade: 0.3,
						area: '500px',
						offset: '30%',
						content:
							'<div style="margin: 10px;">\
                                  <div class="line">\
                                      <div style="font-size: 13px;">Please select a verification method：</div>\
                                      <div class="label-input-group ptb10">\
                                          <select class="bt-input-text" name="auth_to">' +
							options +
							'</select>\
                                          <span class="dnsapi-btn"></span>\
                                          <span class="renew-onkey"><button class="btn btn-success btn-sm mr5" style="margin-left: 10px;" onclick="site.ssl.renew_ssl_other()">One-click renewal</button></span>\
                                      </div>\
                                  </div>\
                                  <ul class="help-info-text c7">\
                                      <li>Wildcard certificate cannot use [File Authentication], please select DNS authentication</li>\
                                      <li>Use [File Authentication], please make sure that [Enable HTTPS / 301 Redirect / Reverse Proxy] and other functions are not enabled.</li>\
                                      <li>Use [Alibaba Cloud DNS] [DnsPod] and other authentication methods to set the correct key</li>\
                                      <li>After the renewal is successful, the certificate will try to renew automatically 30 days before the next expiration</li>\
                                      <li>Using [DNS Authentication-Manual Resolution] Renewed certificate cannot be automatically renewed 30 days before the next expiration</li>\
                                  </ul>\
                                </div>',
						success: function (layers) {
							$("select[name='auth_to']").change(function () {
								var dnsapi = $(this).val();
								$('.dnsapi-btn').html('');
								for (var i = 0; i < cert_init.dnsapi.length; i++) {
									if (cert_init.dnsapi[i].name !== dnsapi) continue;
									acme.dnsapi = cert_init.dnsapi[i];
									if (!cert_init.dnsapi[i].data) continue;
									$('.dnsapi-btn').html('<button class="btn btn-default btn-sm mr5 set_dns_config" onclick="site.ssl.show_dnsapi_setup()">Set</button>');
									if (cert_init.dnsapi[i].data[0].value || cert_init.dnsapi[i].data[1].value) break;
									site.ssl.show_dnsapi_setup();
								}
							});
						},
					});
				});
			}
		},
		//续签其它
		renew_ssl_other: function () {
			var auth_to = $("select[name='auth_to']").val();
			var auth_type = 'http';
			if (auth_to === 'http') {
				if (JSON.stringify(acme.domains).indexOf('*.') !== -1) {
					layer.msg('Domain names containing wildcards cannot use File Authentication (HTTP)!', { icon: 2 });
					return;
				}
				auth_to = acme.id;
			} else {
				if (auth_to !== 'dns') {
					if (auth_to === 'Dns_com') {
						acme.dnsapi.data = [{ value: 'None' }, { value: 'None' }];
					}
					if (!acme.dnsapi.data[0].value || !acme.dnsapi.data[1].value) {
						layer.msg('Please set [' + acme.dnsapi.title + '] interface information first!', { icon: 2 });
						return;
					}
					auth_to = auth_to + '|' + acme.dnsapi.data[0].value + '|' + acme.dnsapi.data[1].value;
				}
				auth_type = 'dns';
			}
			layer.close(acme.select_loadT);
			acme.apply_cert(acme.domains, auth_type, auth_to, '0', function (rdata) {
				site.ssl.ssl_result(rdata, auth_type, acme.siteName);
			});
		},
		show_dnsapi_setup: function () {
			var dnsapi = acme.dnsapi;
			acme.dnsapi_loadT = layer.open({
				title: 'Set [' + dnsapi.title + '] interface',
				type: 1,
				closeBtn: 0,
				shade: 0.3,
				area: '550px',
				offset: '30%',
				content:
					'<div class="bt-form bt-form pd20 pb70 ">\
                          <div class="line ">\
                              <span class="tname" style="width: 125px;">' +
					dnsapi.data[0].key +
					'</span>\
                              <div class="info-r" style="margin-left:135px">\
                                  <input name="' +
					dnsapi.data[0].name +
					'" class="bt-input-text mr5 dnsapi-key" type="text" style="width:330px" value="' +
					dnsapi.data[0].value +
					'">\
                              </div>\
                          </div>\
                          <div class="line ">\
                              <span class="tname" style="width: 125px;">' +
					dnsapi.data[1].key +
					'</span>\
                              <div class="info-r" style="margin-left:135px">\
                                  <input name="' +
					dnsapi.data[1].name +
					'" class="bt-input-text mr5 dnsapi-token" type="text" style="width:330px" value="' +
					dnsapi.data[1].value +
					'">\
                              </div>\
                          </div>\
                          <div class="bt-form-submit-btn">\
                              <button type="button" class="btn btn-sm btn-danger" onclick="layer.close(acme.dnsapi_loadT);">Close</button>\
                              <button type="button" class="btn btn-sm btn-success dnsapi-save">Save</button>\
                          </div>\
                          <ul class="help-info-text c7">\
                              <li>' +
					dnsapi.help +
					'</li>\
                          </ul>\
                        </div>',
				success: function (layers) {
					$('.dnsapi-save').click(function () {
						var dnsapi_key = $('.dnsapi-key');
						var dnsapi_token = $('.dnsapi-token');
						pdata = {};
						pdata[dnsapi_key.attr('name')] = dnsapi_key.val();
						pdata[dnsapi_token.attr('name')] = dnsapi_token.val();
						acme.dnsapi.data[0].value = dnsapi_key.val();
						acme.dnsapi.data[1].value = dnsapi_token.val();
						bt.site.set_dns_api({ pdata: JSON.stringify(pdata) }, function (ret) {
							if (ret.status) layer.close(acme.dnsapi_loadT);
							bt.msg(ret);
						});
					});
				},
			});
		},
		set_cert: function (siteName, res) {
			var loadT = bt.load(lan.site.saving_txt);
			var pdata = {
				type: 1,
				siteName: siteName,
				key: res.private_key,
				csr: res.cert + res.root,
			};
			bt.send('SetSSL', 'site/SetSSL', pdata, function (rdata) {
				loadT.close();
				site.reload();
				layer.msg(res.msg, { icon: 1 });
			});
		},
		show_error: function (res, auth_type) {
			var area_size = '500px';
			var err_info = '';
			if (res.msg[1].challenges === undefined) {
				err_info += '<p><span>Response status:</span>' + res.msg[1].status + '</p>';
				err_info += '<p><span>Error type:</span>' + res.msg[1].type + '</p>';
				err_info += '<p><span>Error code:</span>' + res.msg[1].detail + '</p>';
			} else {
				if (!res.msg[1].challenges[1]) {
					if (res.msg[1].challenges[0]) {
						res.msg[1].challenges[1] = res.msg[1].challenges[0];
					}
				}
				if (res.msg[1].status === 'invalid') {
					area_size = '600px';
					var trs = $('#dns_txt_jx tbody tr');
					var dns_value = '';

					for (var imd = 0; imd < trs.length; imd++) {
						if (trs[imd].outerText.indexOf(res.msg[1].identifier.value) == -1) continue;
						var s_tmp = trs[imd].outerText.split('\t');
						if (s_tmp.length > 1) {
							dns_value = s_tmp[1];
							break;
						}
					}

					err_info += '<p><span>Verify domain name:</span>' + res.msg[1].identifier.value + '</p>';
					if (auth_type === 'dns') {
						var check_url = '_acme-challenge.' + res.msg[1].identifier.value;
						err_info += '<p><span>Verify record:</span>' + check_url + '</p>';
						err_info += '<p><span>Verify content:</span>' + dns_value + '</p>';
						err_info += '<p><span>Error code:</span>' + site.html_encode(res.msg[1].challenges[1].error.detail) + '</p>';
					} else {
						var check_url = 'http://' + res.msg[1].identifier.value + '/.well-known/acme-challenge/' + res.msg[1].challenges[0].token;
						err_info += "<p><span>Verify URL:</span><a class='btlink' href='" + check_url + "' target='_blank'>Click to view</a></p>";
						err_info += '<p><span>Verify content:</span>' + res.msg[1].challenges[0].token + '</p>';
						err_info += '<p><span>Error code:</span>' + site.html_encode(res.msg[1].challenges[0].error.detail) + '</p>';
					}
					err_info += "<p><span>Verify results:</span> <a style='color:red;'>Verify failed</a></p>";
				}
			}

			layer.msg('<div class="ssl-file-error"><a style="color: red;font-weight: 900;">' + res.msg[0] + '</a>' + err_info + '</div>', {
				icon: 2,
				time: 0,
				shade: 0.3,
				shadeClose: true,
				area: area_size,
			});
		},
		ssl_result: function (res, auth_type, siteName) {
			layer.close(acme.loadT);
			if (res.status === false && typeof res.msg === 'string') {
				bt.msg(res);
				return;
			}
			if (res.status === true || res.status === 'pending' || res.save_path !== undefined) {
				if (auth_type == 'dns' && res.status === 'pending') {
					var b_load = bt.open({
						type: 1,
						area: '700px',
						title: 'Manually parse TXT records',
						closeBtn: 2,
						shift: 5,
						shadeClose: false,
						content:
							"<div class='divtable pd15 div_txt_jx'>\
                                  <p class='mb15' >Please do TXT analysis according to the following list:</p>\
                                  <table id='dns_txt_jx' class='table table-hover'></table>\
                                  <div class='text-right mt10'>\
                                      <button class='btn btn-success btn-sm btn_check_txt' >verification</button>\
                                  </div>\
                                  </div>",
					});

					//手动验证事件
					$('.btn_check_txt').click(function () {
						acme.auth_domain(res.index, function (res1) {
							layer.close(acme.loadT);
							if (res1.status === true) {
								b_load.close();
								site.ssl.set_cert(siteName, res1);
							} else {
								site.ssl.show_error(res1, auth_type);
							}
						});
					});

					//显示手动验证信息
					setTimeout(function () {
						var data = [];
						acme_txt = '_acme-challenge.';
						for (var j = 0; j < res.auths.length; j++) {
							data.push({
								name: acme_txt + res.auths[j].domain.replace('*.', ''),
								type: 'TXT',
								txt: res.auths[j].auth_value,
								force: 'Yes',
							});
							data.push({
								name: res.auths[j].domain.replace('*.', ''),
								type: 'CAA',
								txt: '0 issue "letsencrypt.org"',
								force: 'No',
							});
						}
						bt.render({
							table: '#dns_txt_jx',
							columns: [
								{ field: 'name', width: '220px', title: 'Resolving domain names' },
								{ field: 'txt', title: 'Record value' },
								{ field: 'type', title: 'Types of' },
								{ field: 'force', title: 'essential' },
							],
							data: data,
						});
						$('.div_txt_jx').append(
							bt.render_help([
								'It takes some time to resolve the domain name to take effect. After completing all the resolution operations, please wait 1 minute before clicking the verification button.',
								'You can manually verify whether the domain name resolution is effective through CMD commands: nslookup -q=txt ' + acme_txt + res.auths[0].domain.replace('*.', ''),
								'If you are using Pagoda Cloud Resolution Plugin, Alibaba Cloud DNS, DnsPod as DNS, you can use the DNS interface to automatically resolve',
							])
						);
					});
					return;
				}
				site.ssl.set_cert(siteName, res);
				return;
			}

			site.ssl.show_error(res, auth_type);
		},
		get_renew_stat: function () {
			$.post('/ssl?action=Get_Renew_SSL', {}, function (task_list) {
				if (!task_list.status) return;
				var s_body = '';
				var b_stat = false;
				for (var i = 0; i < task_list.data.length; i++) {
					s_body += '<p>' + task_list.data[i].subject + ' >> ' + task_list.data[i].msg + '</p>';
					if (task_list.data[i].status !== true && task_list.data[i].status !== false) {
						b_stat = true;
					}
				}

				if (site.ssl.my_ssl_msg) {
					$('.my-renew-ssl').html(s_body);
				} else {
					site.ssl.my_ssl_msg = layer.msg('<div class="my-renew-ssl">' + s_body + '</div>', {
						time: 0,
						icon: 16,
						shade: 0.3,
					});
				}

				if (!b_stat) {
					setTimeout(function () {
						layer.close(site.ssl.my_ssl_msg);
						site.ssl.my_ssl_msg = null;
					}, 3000);
					return;
				}

				setTimeout(function () {
					site.ssl.get_renew_stat();
				}, 1000);
			});
		},
		onekey_ssl: function (partnerOrderId, siteName) {
			bt.site.get_ssl_info(partnerOrderId, siteName, function (rdata) {
				bt.msg(rdata);
				if (rdata.status) site.reload(7);
			});
		},
		set_ssl_status: function (action, siteName, ssl_id) {
			bt.site.set_ssl_status(action, siteName, function (rdata) {
				bt.msg(rdata);
				if (rdata.status) {
					site.reload(7);
					if (ssl_id != undefined) {
						setTimeout(function () {
							$('#ssl_tabs span:eq(' + ssl_id + ')').click();
						}, 1000);
					}
					if (action == 'CloseSSLConf') {
						layer.msg(lan.site.ssl_close_info, { icon: 1, time: 5000 });
					}
				}
			});
		},
		verify_domain: function (partnerOrderId, siteName) {
			bt.site.verify_domain(partnerOrderId, siteName, function (vdata) {
				bt.msg(vdata);
				if (vdata.status) {
					if (vdata.data.stateCode == 'COMPLETED') {
						site.ssl.onekey_ssl(partnerOrderId, siteName);
					} else {
						layer.msg('Waiting for CA verification, if it fails to verify successfully for a long time, please log in to the official website and use DNS to re-apply...');
					}
				}
			});
		},
		reload: function (index) {
			if (index == undefined) index = 0;
			var _sel = $('#ssl_tabs .on');
			if (_sel.length == 0) _sel = $('#ssl_tabs span:eq(0)');
			_sel.trigger('click');
		},
		set_auto_restart_rph: function (sitename) {
			var $checkbox = $('#auto_restart_rph');
			var checked = $checkbox.is(':checked');
			var url = checked ? 'remove_auto_restart_rph' : 'auto_restart_rph';
			var loadT = bt.load(lan.site.the_msg);
			$.post(
				'/site?action=' + url,
				{
					sitename: sitename,
				},
				function (res) {
					loadT.close();
					bt.msg(res);
					if (res.status) {
						$checkbox.prop('checked', !checked);
					}
				}
			);
		},
	},
	edit: {
		update_composer: function () {
			loadT = bt.load();
			$.post(
				'/files?action=update_composer',
				{
					repo: $("select[name='repo']").val(),
				},
				function (v_data) {
					loadT.close();
					bt.msg(v_data);
				}
			);
		},
		show_composer_log: function () {
			$.post(
				'/ajax?action=get_lines',
				{
					filename: '/tmp/composer.log',
					num: 30,
				},
				function (v_body) {
					var log_obj = $('#composer-log');
					if (log_obj.length < 1) return;
					log_obj.html(v_body.msg);
					var div = document.getElementById('composer-log');
					div.scrollTop = div.scrollHeight;
					if (v_body.msg.indexOf('BT-Exec-Completed') != -1) {
						//layer.close(site.edit.comp_showlog);
						layer.msg('Execution complete', {
							icon: 1,
						});
						return;
					}

					setTimeout(function () {
						site.edit.show_composer_log();
					}, 1000);
				}
			);
		},
		comp_confirm: 0,
		comp_showlog: 0,
		exec_composer: function () {
			site.edit.comp_confirm = layer.confirm(
				'The impact of Composer execution depends on the composer.json configuration file in this directory. Continue?',
				{
					title: 'Execute composer',
					closeBtn: 2,
					icon: 3,
				},
				function (index) {
					layer.close(site.edit.comp_confirm);
					var pdata = {
						php_version: $("select[name='php_version']").val(),
						composer_args: $("select[name='composer_args']").val(),
						composer_cmd: $("input[name='composer_cmd']").val(),
						repo: $("select[name='repo']").val(),
						path: $("input[name='composer_path']").val(),
						user: $("select[name='composer_user']").val(),
					};
					$.post('/files?action=exec_composer', pdata, function (rdatas) {
						if (!rdatas.status) {
							layer.msg(rdatas.msg, {
								icon: 2,
							});
							return false;
						}
						if (rdatas.status === true) {
							site.edit.comp_showlog = layer.open({
								area: '800px',
								type: 1,
								shift: 5,
								closeBtn: 2,
								title: 'Execute Composer in the [' + pdata['path'] + '] directory. After execution, please close this window after confirming that there is no problem',
								content: "<pre id='composer-log' style='height: 300px;background-color: #333;color: #fff;margin: 0 0 0;'></pre>",
							});
							setTimeout(function () {
								site.edit.show_composer_log();
							}, 200);
						}
					});
				}
			);
		},
		remove_composer_lock: function (path) {
			$.post(
				'/files?action=DeleteFile',
				{
					path: path + '/composer.lock',
				},
				function (rdata) {
					bt.msg(rdata);
					$('.composer-msg').remove();
					$('.composer-rm').remove();
				}
			);
		},
		set_composer: function (web) {
			$.post(
				'/files?action=get_composer_version',
				{
					path: web.path,
				},
				function (v_data) {
					if (v_data.status === false) {
						bt.msg(v_data);
						return;
					}

					var php_versions = '';
					for (var i = 0; i < v_data.php_versions.length; i++) {
						if (v_data.php_versions[i].version == '00') continue;
						php_versions += '<option value="' + v_data.php_versions[i].version + '">' + v_data.php_versions[i].name + '</option>';
					}

					var msg = '';
					if (v_data.comp_lock) {
						msg += '<span>' + v_data.comp_lock + ' <a class="btlink composer-rm" onclick="site.edit.remove_composer_lock(\'' + web.path + '\')">[Delete]</a></span>';
					}
					if (v_data.comp_json !== true) {
						msg += '<span>' + v_data.comp_json + '</span>';
					}

					var com_body =
						'<from class="bt-form" style="padding:10px 0px 0px 0px;;display:inline-block;width:580px; height: auto;">' +
						'<div class="line"><span style="width: 105px;" class="tname">Version</span><div class="info-r"><input readonly="readonly" style="background-color: #eee;width:180px;" name="composer_version" class="bt-input-text" value="' +
						v_data.msg +
						'" /><button onclick="site.edit.update_composer();" style="margin-left: 5px;" class="btn btn-default btn-sm">Update</button></div></div>' +
						'<div class="line"><span style="width: 105px;" class="tname">PHP</span><div class="info-r">' +
						'<select class="bt-input-text" name="php_version" style="width:180px;">' +
						'<option value="auto">Auto</option>' +
						php_versions +
						'</select>' +
						'</div></div>' +
						'<div class="line"><span style="width: 105px;" class="tname">Parameters</span><div class="info-r">' +
						'<select class="bt-input-text" name="composer_args" style="width:180px;">' +
						'<option value="install">Install</option>' +
						'<option value="update">Update</option>' +
						'</select>' +
						'</div></div>' +
						'<div class="line"><span style="width: 105px;" class="tname">Extra commands</span><div class="info-r">' +
						'<input style="width:275px;" class="bt-input-text" id="composer_cmd" name="composer_cmd"  placeholder="App name or full Composer command" type="text" value="" />' +
						'</div></div>' +
						'<div class="line"><span style="width: 105px;" class="tname">Source</span><div class="info-r">' +
						'<select class="bt-input-text" name="repo" style="width:180px;">' +
						'<option value="repos.packagist">Official(packagist.org)</option>' +
						'</select>' +
						'</div></div>' +
						'<div class="line"><span style="width: 105px;" class="tname">User</span><div class="info-r">' +
						'<select class="bt-input-text" name="composer_user" style="width:180px;">' +
						'<option value="www">www(recommend)</option>' +
						'<option value="root">root(not suggested)</option>' +
						'</select>' +
						'</div></div>' +
						'<div class="line"><span style="width: 105px;" class="tname">Dir</span><div class="info-r">' +
						'<input style="width:275px;" class="bt-input-text" id="composer_path" name="composer_path" type="text" value="' +
						web.path +
						'" /><span class="glyphicon glyphicon-folder-open cursor ml5" onclick="bt.select_path(\'composer_path\')"></span>' +
						'</div></div>' +
						'<div class="line"><span style="width: 105px;height: 25px;" class="tname"> </span><span class="composer-msg" style="color:red;">' +
						msg +
						'</span></div>' +
						'<div class="line" style="clear:both"><span style="width: 105px;" class="tname"> </span><div class="info-r"><button class="btn btn-success btn-sm" onclick="site.edit.exec_composer()">Execute</button></div></div>' +
						'</from>' +
						'<ul class="help-info-text c7">' +
						'<li>Directory：Website root dir by default, please make sure that the dir contains composer.json</li>' +
						'<li>User：The default user www, unless your website is run with root privileges, it is not recommended to use the root user to execute composer</li>' +
						'<li>Source：source of composer</li>' +
						'<li>Parameters：Install (install dependent package), Update (upgrade dependent package), please select as needed</li>' +
						'<li>Extra commands: If this is empty, it will be executed according to the conf in composer.json, Supported fill in the complete composer command</li>' +
						'<li>PHP version：The PHP version used to execute composer, it is recommended to try the default, if the installation fails, try to choose another PHP version</li>' +
						'<li>Composer version：Composer version, you can click [Upgrade Composer] on the right to upgrade Composer to the latest stable version</li>' +
						'</ul>';
					$('#webedit-con').html(com_body);
				}
			);
		},
		set_domains: function (web) {
			var _this = this;
			var list = [
				{
					items: [
						{ name: 'newdomain', width: '400px', type: 'textarea', placeholder: lan.site.domain_help },
						{
							name: 'btn_submit_domain',
							text: lan.site.add,
							type: 'button',
							callback: function (sdata) {
								var arrs = sdata.newdomain.split('\n');
								var domins = '';
								for (var i = 0; i < arrs.length; i++) domins += arrs[i] + ',';
								bt.site.add_domains(web.id, web.name, bt.rtrim(domins, ','), function (ret) {
									if (ret.status) site.reload(0);
								});
							},
						},
					],
				},
			];
			var _form_data = bt.render_form_line(list[0]),
				loadT = null,
				placeholder = null;
			$('#webedit-con').html(_form_data.html + "<div class='bt_table' id='domain_table' style='height:350px;overflow:auto'></div>");
			bt.render_clicks(_form_data.clicks);
			$('.btn_submit_domain').addClass('pull-right').css('margin', '30px 35px 0 0');
			placeholder = $('.placeholder');
			placeholder
				.click(function () {
					$(this).hide();
					$('.newdomain').focus();
				})
				.css({
					width: '340px',
					heigth: '100px',
					left: '0px',
					top: '0px',
					'padding-top': '10px',
					'padding-left': '15px',
				});
			$('.newdomain')
				.focus(function () {
					placeholder.hide();
					loadT = layer.tips(placeholder.html(), $(this), { tips: [1, '#20a53a'], time: 0, area: $(this).width() });
				})
				.blur(function () {
					if ($(this).val().length == 0) placeholder.show();
					layer.close(loadT);
				});

			bt_tools.table({
				el: '#domain_table',
				url: '/data?action=getData',
				param: { table: 'domain', list: 'True', search: web.id },
				dataFilter: function (res) {
					return { data: res };
				},
				column: [
					{ type: 'checkbox', width: 20, keepNumber: 1 },
					{
						fid: 'name',
						title: lan.site.domain,
						template: function (row) {
							return '<a href="http://' + row.name + ':' + row.port + '" target="_blank" class="btlink">' + row.name + '</a>';
						},
					},
					{ fid: 'port', title: lan.site.port, width: 50, type: 'text' },
					{
						title: 'OPT',
						width: 80,
						type: 'group',
						align: 'right',
						group: [
							{
								title: 'Del',
								template: function (row, that) {
									return that.data.length === 1 ? '<span>Inoperable</span>' : 'Del';
								},
								event: function (row, index, ev, key, that) {
									if (that.data.length === 1) {
										bt.msg({ status: false, msg: 'The last domain name cannot be deleted!' });
										return false;
									}
									bt.confirm(
										{
											title: 'Delete domain [ ' + row.name + ' ]',
											msg: lan.site.domain_del_confirm,
										},
										function () {
											bt.site.del_domain(web.id, web.name, row.name, row.port, function (res) {
												if (res.status) that.$delete_table_row(index);
												bt.msg(res);
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
						// 批量操作
						type: 'batch',
						positon: ['left', 'bottom'],
						config: {
							title: ' delete',
							url: '/site?action=delete_domain_multiple',
							param: { id: web.id },
							paramId: 'id',
							paramName: 'domains_id',
							theadName: 'Domain',
							confirmVerify: false, //是否提示验证方式
							refresh: true,
						},
					},
				],
			});
			$('#domain_table>.divtable').css('max-height', '350px');
		},
		set_dirbind: function (web) {
			var _this = this;
			$('#webedit-con').html('<div id="sub_dir_table"></div>');
			bt_tools.table({
				el: '#sub_dir_table',
				url: '/site?action=GetDirBinding',
				param: { id: web.id },
				dataFilter: function (res) {
					if ($('#webedit-con').children().length === 2) return { data: res.binding };
					var dirs = [];
					for (var n = 0; n < res.dirs.length; n++) dirs.push({ title: res.dirs[n], value: res.dirs[n] });
					var data = {
						title: '',
						class: 'mb0',
						items: [
							{ title: lan.site.domain, width: '140px', name: 'domain' },
							{ title: lan.site.subdirectories, name: 'dirName', type: 'select', items: dirs },
							{
								text: lan.site.add,
								type: 'button',
								name: 'btn_add_subdir',
								callback: function (sdata) {
									if (!sdata.domain || !sdata.dirName) {
										layer.msg(lan.site.d_s_empty, { icon: 2 });
										return;
									}
									bt.site.add_dirbind(web.id, sdata.domain, sdata.dirName, function (ret) {
										layer.msg(ret.msg, { icon: ret.status ? 1 : 2 });
										if (ret.status) site.reload(1);
									});
								},
							},
						],
					};
					var _form_data = bt.render_form_line(data);
					$('#webedit-con').prepend(_form_data.html);
					bt.render_clicks(_form_data.clicks);
					return { data: res.binding };
				},
				column: [
					{ type: 'checkbox', width: 20, keepNumber: 1 },
					{ fid: 'domain', title: lan.site.domain, type: 'text' },
					{ fid: 'port', title: lan.site.port, width: 70, type: 'text' },
					{ fid: 'path', title: lan.site.subdirectories, width: 70, type: 'text' },
					{
						title: 'Opt',
						width: 130,
						type: 'group',
						align: 'right',
						group: [
							{
								title: 'URL rewrite',
								event: function (row, index, ev, key, that) {
									bt.site.get_dir_rewrite({ id: row.id }, function (ret) {
										if (!ret.status) {
											var confirmObj = layer.confirm(
												lan.site.url_rewrite_alter,
												{
													icon: 3,
													closeBtn: 2,
												},
												function () {
													bt.site.get_dir_rewrite({ id: row.id, add: 1 }, function (ret) {
														layer.close(confirmObj);
														show_dir_rewrite(ret);
													});
												}
											);
											return;
										}
										show_dir_rewrite(ret);

										function get_rewrite_file(name) {
											var spath = '/www/server/panel/rewrite/' + (bt.get_cookie('serverType') == 'openlitespeed' ? 'apache' : bt.get_cookie('serverType')) + '/' + name + '.conf';
											if (bt.get_cookie('serverType') == 'nginx') {
												if (name == 'default') spath = '/www/server/panel/vhost/rewrite/' + web.name + '_' + row['path'] + '.conf';
											} else {
												if (name == 'default') spath = '/www/wwwroot/' + web.name + '/' + row['path'] + '.htaccess';
											}
											bt.files.get_file_body(spath, function (sdata) {
												$('.dir_config').text(sdata.data);
											});
										}

										function show_dir_rewrite(ret) {
											var load_form = bt.open({
												type: 1,
												area: ['510px', '530px'],
												title: lan.site.config_url,
												closeBtn: 2,
												shift: 5,
												skin: 'bt-w-con',
												shadeClose: true,
												content: "<div class='bt-form webedit-dir-box dir-rewrite-man-con'></div>",
												success: function () {
													var _html = $('.webedit-dir-box'),
														arrs = [];
													for (var i = 0; i < ret.rlist.length; i++) {
														if (i == 0) {
															arrs.push({ title: ret.rlist[i], value: 'default' });
														} else {
															arrs.push({ title: ret.rlist[i], value: ret.rlist[i] });
														}
													}
													var datas = [
														{
															name: 'dir_rewrite',
															type: 'select',
															width: '130px',
															items: arrs,
															callback: function (obj) {
																get_rewrite_file(obj.val());
															},
														},
														{
															items: [
																{
																	name: 'dir_config',
																	type: 'textarea',
																	value: ret.data,
																	width: '470px',
																	height: '260px',
																},
															],
														},
														{
															items: [
																{
																	name: 'btn_save',
																	text: 'Save',
																	type: 'button',
																	callback: function (ldata) {
																		// console.log(ret)
																		bt.files.set_file_body(ret.filename, ldata.dir_config, 'utf-8', function (sdata) {
																			if (sdata.status) load_form.close();
																			bt.msg(sdata);
																		});
																	},
																},
															],
														},
													];
													var clicks = [];
													for (var i = 0; i < datas.length; i++) {
														var _form_data = bt.render_form_line(datas[i]);
														_html.append(_form_data.html);
														var _other =
															bt.os == 'Linux' && i == 0 ? '<span>Rewrite rule converter：<a href="https://www.bt.cn/Tools" target="_blank" style="color:#20a53a">Apache to Nginx</a></span>' : '';
														_html.find('.info-r').append(_other);
														clicks = clicks.concat(_form_data.clicks);
													}
													_html.append(
														bt.render_help([
															'Please select your application.',
															'If the site cannot be accessed after the rewrite rules set, please try to reset to default.',
															'You are able to modify rewrite rules, just save it after modification.',
														])
													);
													bt.render_clicks(clicks);
													get_rewrite_file($('.dir_rewrite option:eq(0)').val());
												},
											});
										}
									});
								},
							},
							{
								title: 'Del',
								event: function (row, index, ev, key, that) {
									bt.confirm(
										{
											title: 'Are you sure to delete this【' + row.path + '】 subdirectory binding?',
											msg: lan.site.s_bin_del,
										},
										function () {
											bt.site.del_dirbind(row.id, function (res) {
												if (res.status) that.$delete_table_row(index);
												bt.msg(res);
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
						// 批量操作
						type: 'batch',
						positon: ['left', 'bottom'],
						config: {
							title: ' execute',
							url: '/site?action=delete_dir_bind_multiple',
							param: { id: web.id },
							paramId: 'id',
							paramName: 'bind_ids',
							theadName: 'Domain',
							confirmVerify: false, //是否提示验证方式
						},
					},
				],
			});
		},
		set_dirpath: function (web) {
			var loading = bt.load();
			bt.site.get_site_path(web.id, function (path) {
				bt.site.get_dir_userini(web.id, path, function (rdata) {
					loading.close();
					var dirs = [];
					var is_n = false;
					for (var n = 0; n < rdata.runPath.dirs.length; n++) {
						dirs.push({ title: rdata.runPath.dirs[n], value: rdata.runPath.dirs[n] });
						if (rdata.runPath.runPath === rdata.runPath.dirs[n]) is_n = true;
					}
					if (!is_n) dirs.push({ title: rdata.runPath.runPath, value: rdata.runPath.runPath });
					var datas = [
						{
							title: '',
							items: [
								{
									name: 'userini',
									type: 'checkbox',
									text: lan.site.anti_XSS_attack + '(open_basedir)',
									value: rdata.userini,
									callback: function (sdata) {
										bt.site.set_dir_userini(path, web.id, function (ret) {
											if (ret.status) site.reload(2);
											layer.msg(ret.msg, { icon: ret.status ? 1 : 2 });
										});
									},
								},
								{
									name: 'logs',
									type: 'checkbox',
									text: lan.site.write_access_log,
									value: rdata.logs,
									callback: function (sdata) {
										bt.site.set_logs_status(web.id, function (ret) {
											if (ret.status) site.reload(2);
											layer.msg(ret.msg, { icon: ret.status ? 1 : 2 });
										});
									},
								},
							],
						},
						{
							title: '',
							items: [
								{
									name: 'path',
									title: lan.site.site_menu_2,
									width: '240px',
									value: path,
									add_class: 'ml5',
									event: {
										css: 'glyphicon-folder-open',
										callback: function (obj) {
											bt.select_path(obj);
										},
									},
								},
								{
									name: 'btn_site_path',
									type: 'button',
									text: lan.site.save,
									callback: function (pdata) {
										bt.site.set_site_path_new(web.id, pdata.path, web.name, function (ret) {
											if (ret.status) site.reload(2);
											layer.msg(ret.msg, { icon: ret.status ? 1 : 2 });
										});
									},
								},
							],
						},
						{
							title: '',
							items: [
								{
									title: lan.site.run_dir,
									width: '240px',
									value: rdata.runPath.runPath,
									name: 'dirName',
									type: 'select',
									add_class: 'ml5 mr20',
									items: dirs,
								},
								{
									name: 'btn_run_path',
									type: 'button',
									text: lan.site.save,
									callback: function (pdata) {
										bt.site.set_site_runpath(web.id, pdata.dirName, function (ret) {
											if (ret.status) site.reload(2);
											layer.msg(ret.msg, { icon: ret.status ? 1 : 2 });
										});
									},
								},
							],
						},
					];
					var _html = $("<div class='webedit-box soft-man-con'></div>");
					var clicks = [];
					for (var i = 0; i < datas.length; i++) {
						var _form_data = bt.render_form_line(datas[i]);
						_html.append($(_form_data.html).addClass('line mtb10'));
						clicks = clicks.concat(_form_data.clicks);
					}
					_html.find('input[name="path"]').parent().css('padding-left', '27px');
					_html.find('input[type="checkbox"]').parent().addClass('label-input-group ptb10');
					_html.find('button[name="btn_run_path"]').addClass('ml45');
					_html.find('button[name="btn_site_path"]').addClass('ml33');
					_html.append(bt.render_help([lan.site.specify_subdir]));
					if (bt.os == 'Linux')
						_html.append(
							'<div class="user_pw_tit" style="margin-top: 2px;padding-top: 11px;"><span class="tit">' +
								lan.site.pass_visit +
								'</span><span class="btswitch-p"><input class="btswitch btswitch-ios" id="pathSafe" type="checkbox"><label class="btswitch-btn phpmyadmin-btn" for="pathSafe" ></label></span></div><div class="user_pw" style="margin-top: 10px; display: block;"></div>'
						);

					$('#webedit-con').append(_html);
					bt.render_clicks(clicks);
					$('#pathSafe').click(function () {
						var val = $(this).prop('checked');
						var _div = $('.user_pw');
						if (val) {
							var dpwds = [
								{
									title: lan.site.access_account,
									width: '250px',
									name: 'username_get',
									placeholder: lan.site.no_change_set_empty,
								},
								{
									title: lan.site.pass_visit,
									width: '250px',
									type: 'password',
									name: 'password_get_1',
									placeholder: lan.site.no_change_set_empty,
								},
								{
									title: lan.site.pass_again,
									width: '250px',
									type: 'password',
									name: 'password_get_2',
									placeholder: lan.site.no_change_set_empty,
								},
								{
									name: 'btn_password_get',
									text: lan.site.save,
									type: 'button',
									callback: function (rpwd) {
										if (rpwd.password_get_1 != rpwd.password_get_2) {
											layer.msg(lan.bt.pass_err_re, { icon: 2 });
											return;
										}
										bt.site.set_site_pwd(web.id, rpwd.username_get, rpwd.password_get_1, function (ret) {
											layer.msg(ret.msg, { icon: ret.status ? 1 : 2 });
											if (ret.status) site.reload(2);
										});
									},
								},
							];
							for (var i = 0; i < dpwds.length; i++) {
								var _from_pwd = bt.render_form_line(dpwds[i]);
								_div.append('<div>' + _from_pwd.html + '</div>');
								bt.render_clicks(_from_pwd.clicks);
							}
						} else {
							bt.site.close_site_pwd(web.id, function (rdata) {
								layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
								_div.html('');
							});
						}
					});
					if (rdata.pass) $('#pathSafe').trigger('click');
				});
			});
		},
		set_dirguard: function (web) {
			$('#webedit-con').html('<div id="set_dirguard"></div>');
			var tab =
				'<div class="tab-nav mb15">\
                  <span class="on">Limit access</span><span class="">Deny access</span>\
                  </div>\
                  <div id="dir_dirguard"></div>\
                  <div id="php_dirguard" style="display:none;"></div>';
			$('#set_dirguard').html(tab);
			var dir_dirguard = bt_tools.table({
				el: '#dir_dirguard',
				url: '/site?action=get_dir_auth',
				param: { id: web.id },
				dataFilter: function (res) {
					return { data: res[web.name] };
				},
				column: [
					{ type: 'checkbox', width: 20 },
					{ fid: 'name', title: lan.site.name, type: 'text' },
					{ fid: 'site_dir', title: 'Path', type: 'text' },
					{
						title: lan.site.operate,
						width: 110,
						type: 'group',
						align: 'right',
						group: [
							{
								title: lan.site.edit,
								event: function (row, index, ev, key, that) {
									site.edit.template_Dir(web.id, false, row);
								},
							},
							{
								title: lan.site.del,
								event: function (row, index, ev, key, that) {
									bt.site.delete_dir_guard(web.id, row.name, function (res) {
										if (res.status) that.$delete_table_row(index);
										bt.msg(res);
									});
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
								title: 'Add limit access',
								active: true,
								event: function (ev) {
									site.edit.template_Dir(web.id, true);
								},
							},
						],
					},
					{
						// 批量操作
						type: 'batch',
						positon: ['left', 'bottom'],
						config: {
							title: ' delete',
							url: '/site?action=delete_dir_auth',
							param: function (row) {
								return {
									id: web.id,
									name: row.name,
								};
							},
							load: true,
							callback: function (that) {
								// 手动执行,data参数包含所有选中的站点
								bt.show_confirm('Delete limit access', 'Do you want to delete limit access ?', function () {
									that.start_batch({}, function (list) {
										var html = '';
										for (var i = 0; i < list.length; i++) {
											var item = list[i];
											html += '<tr><td>' + item.name + '</td><td class="text-right"><span style="color:' + (item.request.status ? '#20a53a' : 'red') + '">' + item.request.msg + '</span></td></tr>';
										}
										dir_dirguard.$batch_success_table({
											title: 'Limit access',
											th: 'Limit access name',
											html: html,
										});
										dir_dirguard.$refresh_table_list(true);
									});
								});
							},
						},
					},
				],
			});
			var php_dirguard = bt_tools.table({
				el: '#php_dirguard',
				url: '/config?action=get_file_deny',
				param: {
					website: web.name,
				},
				dataFilter: function (res) {
					return {
						data: res,
					};
				},
				column: [
					{ type: 'checkbox', width: 20 },
					{
						fid: 'name',
						title: lan.site.name,
						type: 'text',
					},
					{
						fid: 'dir',
						title: 'Path',
						type: 'text',
						template: function (row) {
							return '<span title="' + row.dir + '" style="max-width: 250px;" class="limit-text-length">' + row.dir + '</span>';
						},
					},
					{
						fid: 'suffix',
						title: 'Suffix',
						template: function (row) {
							return '<span title="' + row.suffix + '" style="max-width: 85px;" class="limit-text-length">' + row.suffix + '</span>';
						},
					},
					{
						title: lan.site.operate,
						width: 110,
						type: 'group',
						align: 'right',
						group: [
							{
								title: lan.site.edit,
								event: function (row, index, ev, key, that) {
									site.edit.template_php(web.name, row);
								},
							},
							{
								title: lan.site.del,
								event: function (row, index, ev, key, that) {
									site.edit.del_php_deny(web.name, row.name, function (res) {
										if (res.status) that.$delete_table_row(index);
										bt.msg(res);
									});
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
								title: 'Add deny access',
								active: true,
								event: function (ev) {
									site.edit.template_php(web.name);
								},
							},
						],
					},
					{
						// 批量操作
						type: 'batch',
						positon: ['left', 'bottom'],
						config: {
							title: ' delete',
							url: '/site?action=del_file_deny',
							param: function (row) {
								return {
									website: web.name,
									deny_name: row.name,
								};
							},
							load: true,
							callback: function (that) {
								// 手动执行,data参数包含所有选中的站点
								bt.show_confirm('Delete deny access', 'Do you want to delete deny access?', function () {
									that.start_batch({}, function (list) {
										var html = '';
										for (var i = 0; i < list.length; i++) {
											var item = list[i];
											html +=
												'<tr><td>' +
												item.name +
												'</td><td><div style="float:right;"><span style="color:' +
												(item.request.status ? '#20a53a' : 'red') +
												'">' +
												item.request.msg +
												'</span></div></td></tr>';
										}
										php_dirguard.$batch_success_table({
											title: 'Deny access',
											th: 'Deny access name',
											html: html,
										});
										php_dirguard.$refresh_table_list(true);
									});
								});
							},
						},
					},
				],
			});
			$('#dir_dirguard>.divtable,#php_dirguard>.divtable').css('max-height', '340px');
			$('#dir_dirguard').append(
				"<ul class='help-info-text c7'>\
              <li>After setting, you need to enter the password to access it.</li>\
              <li>For example, if I set the limit path /test/ , then I need to enter the account password to access http://aaa.com/test/</li>\
          </ul>"
			);
			$('#php_dirguard').append(
				"<ul class='help-info-text c7'>\
              <li>Suffix: Indicates the suffix that is not allowed to access, if there are more than one, separate with'|'.</li>\
              <li>Path: Quote rules in this directory. e.g: /a/ </li>\
              <li>For Example, if you want to deny http://test.com/a/index.php</li>\
              <li>Please fill in [ /a/ ]</li>\
          </ul>"
			);
			$('#set_dirguard').on('click', '.tab-nav span', function () {
				var index = $(this).index();
				$(this).addClass('on').siblings().removeClass('on');
				if (index == 0) {
					$('#dir_dirguard').show();
					$('#php_dirguard').hide();
				} else {
					$('#php_dirguard').show();
					$('#dir_dirguard').hide();
				}
			});
		},
		ols_cache: function (web) {
			bt.send('get_ols_static_cache', 'config/get_ols_static_cache', { id: web.id }, function (rdata) {
				var clicks = [],
					newkey = [],
					newval = [],
					checked = false;
				Object.keys(rdata).forEach(function (key) {
					//for (let key in rdata) {
					newkey.push(key);
					newval.push(rdata[key]);
				});
				var datas = [
						{ title: newkey[0], name: newkey[0], width: '30%', value: newval[0] },
						{ title: newkey[1], name: newkey[1], width: '30%', value: newval[1] },
						{ title: newkey[2], name: newkey[2], width: '30%', value: newval[2] },
						{ title: newkey[3], name: newkey[3], width: '30%', value: newval[3] },
						{
							name: 'static_save',
							text: lan.site.save,
							type: 'button',
							callback: function (ldata) {
								var cdata = {},
									loadT = bt.load();
								Object.assign(cdata, ldata);
								delete cdata.static_save;
								delete cdata.maxage;
								delete cdata.exclude_file;
								delete cdata.private_save;
								bt.send(
									'set_ols_static_cache',
									'config/set_ols_static_cache',
									{
										values: JSON.stringify(cdata),
										id: web.id,
									},
									function (res) {
										loadT.close();
										bt.msg(res);
									}
								);
							},
						},
						{ title: 'test', name: 'test', width: '30%', value: '11' },
						{ title: 'maxage', name: 'maxage', width: '30%', value: '43200' },
						{ title: 'exclude file', name: 'exclude_file', width: '35%', value: 'fdas.php' },
						{
							name: 'private_save',
							text: lan.site.save,
							type: 'button',
							callback: function (ldata) {
								var edata = {},
									loadT = bt.load();
								if (checked) {
									edata.id = web.id;
									edata.max_age = parseInt($("input[name='maxage']").val());
									edata.exclude_file = $("textarea[name='exclude_file']").val();
									bt.send('set_ols_private_cache', 'config/set_ols_private_cache', edata, function (res) {
										loadT.close();
										bt.msg(res);
									});
								}
							},
						},
					],
					_html = $('<div class="ols"></div>');
				for (var i = 0; i < datas.length; i++) {
					var _form_data = bt.render_form_line(datas[i]);
					_html.append(_form_data.html);
					clicks = clicks.concat(_form_data.clicks);
				}
				$('#webedit-con').append(_html);
				$("input[name='exclude_file']").parent().removeAttr('class').html('<textarea name="exclude_file" class="bt-input-text mr5 exclude_file" style="width:35%;height: 130px;"></textarea>');
				$("input[name='test']")
					.parent()
					.parent()
					.html(
						'<div style="padding-left: 29px;border-top: #ccc 1px dashed;margin-top: -7px;"><em style="float: left;color: #555;font-style: normal;line-height: 32px;padding-right: 2px;">private cache</em><div style="margin-left: 95px;padding-top: 5px;"><input class="btswitch btswitch-ios" id="ols" type="checkbox"><label class="btswitch-btn" for="ols"></label></div></div>'
					);
				var private = $("input[name='maxage'],textarea[name='exclude_file'],button[name='private_save']").parent().parent();
				$('input.bt-input-text').parent().append('<span>sec</span>');
				$("button[name='static_save']")
					.parent()
					.append(bt.render_help(['The default static file cache time is 604800 seconds', 'If you want to shut down, please change it to 0 seconds']));
				$('.ols').append(bt.render_help(['Private cache only supports page caching for PHP and cache time is 120 seconds by default', 'Exclude files only support files with PHP as the suffix']));
				private.hide();
				bt.send('get_ols_private_cache_status', 'config/get_ols_private_cache_status', { id: web.id }, function (kdata) {
					checked = kdata;
					if (kdata) {
						bt.send('get_ols_private_cache', 'config/get_ols_private_cache', { id: web.id }, function (fdata) {
							$("input[name='maxage']").val(fdata.maxage);
							var ss = fdata.exclude_file.join('&#13;');
							$("textarea[name='exclude_file']").html(ss);
							$('#ols').attr('checked', true);
							private.show();
						});
					}
				});
				$('#ols').on('click', function () {
					var loadT = bt.load();
					bt.send('switch_ols_private_cache', 'config/switch_ols_private_cache', { id: web.id }, function (res) {
						loadT.close();
						private.toggle();
						checked = private.is(':hidden') ? false : true;
						bt.msg(res);
						if (checked) {
							bt.send('get_ols_private_cache', 'config/get_ols_private_cache', { id: web.id }, function (fdata) {
								private.show();
								$("input[name='maxage']").val(fdata.maxage);
								$("textarea[name='exclude_file']").html(fdata.exclude_file.join('&#13;'));
							});
						}
					});
				});
				bt.render_clicks(clicks);
				$("button[name='private_save']").parent().css('margin-bottom', '-13px');
				$('.ss-text').css('margin-left', '66px');
				$('.ols .btn-success').css('margin-left', '125px');
			});
		},
		limit_network: function (web) {
			bt.site.get_limitnet(web.id, function (rdata) {
				var limits = [
					{ title: lan.site.bbs_or_blog, value: 1, items: { perserver: 300, perip: 25, limit_rate: 512 } },
					{ title: lan.site.photo_station, value: 2, items: { perserver: 200, perip: 10, limit_rate: 1024 } },
					{ title: lan.site.download_station, value: 3, items: { perserver: 50, perip: 3, limit_rate: 2048 } },
					{ title: lan.site.mall, value: 4, items: { perserver: 500, perip: 10, limit_rate: 2048 } },
					{ title: lan.site.portal_site, value: 5, items: { perserver: 400, perip: 15, limit_rate: 1024 } },
					{ title: lan.site.enterprise, value: 6, items: { perserver: 60, perip: 10, limit_rate: 512 } },
					{ title: lan.site.video, value: 7, items: { perserver: 150, perip: 4, limit_rate: 1024 } },
				];
				var datas = [
					{
						items: [
							{
								name: 'status',
								type: 'checkbox',
								value: rdata.perserver != 0 ? true : false,
								text: lan.site.limit_net_8,
								callback: function (ldata) {
									if (ldata.status) {
										bt.site.set_limitnet(web.id, ldata.perserver, ldata.perip, ldata.limit_rate, function (ret) {
											layer.msg(ret.msg, { icon: ret.status ? 1 : 2 });
											if (ret.status) site.reload(3);
										});
									} else {
										bt.site.close_limitnet(web.id, function (ret) {
											layer.msg(ret.msg, { icon: ret.status ? 1 : 2 });
											if (ret.status) site.reload(3);
										});
									}
								},
							},
						],
					},
					{
						title: lan.site.limit_net_9 + '  ',
						width: '160px',
						name: 'limit',
						type: 'select',
						items: limits,
						callback: function (obj) {
							var data = limits.filter(function (p) {
								return p.value === parseInt(obj.val());
							})[0];
							for (var key in data.items) $('input[name="' + key + '"]').val(data.items[key]);
						},
					},
					{
						title: lan.site.limit_net_10 + '   ',
						type: 'number',
						width: '200px',
						value: rdata.perserver,
						name: 'perserver',
					},
					{
						title: lan.site.limit_net_12 + '   ',
						type: 'number',
						width: '200px',
						value: rdata.perip,
						name: 'perip',
					},
					{
						title: lan.site.limit_net_14 + '   ',
						type: 'number',
						width: '200px',
						value: rdata.limit_rate,
						name: 'limit_rate',
					},
					{
						name: 'btn_limit_get',
						text: lan.site.save,
						type: 'button',
						callback: function (ldata) {
							bt.site.set_limitnet(web.id, ldata.perserver, ldata.perip, ldata.limit_rate, function (ret) {
								layer.msg(ret.msg, { icon: ret.status ? 1 : 2 });
								if (ret.status) site.reload(3);
							});
						},
					},
				];
				var _html = $("<div class='webedit-box soft-man-con newnanme'></div>");
				var clicks = [];
				for (var i = 0; i < datas.length; i++) {
					var _form_data = bt.render_form_line(datas[i]);
					_html.append(_form_data.html);
					clicks = clicks.concat(_form_data.clicks);
				}
				_html.find('input[type="checkbox"]').parent().addClass('label-input-group ptb10');
				_html.append(bt.render_help([lan.site.limit_net_11, lan.site.limit_net_13, lan.site.limit_net_15]));
				$('#webedit-con').append(_html);
				$('.newnanme .tname').css('width', '138px');
				bt.render_clicks(clicks);
				if (rdata.perserver == 0) $("select[name='limit']").trigger('change');
				$('#status,.btn_limit_get').css('margin-left', '138px');
			});
		},
		get_rewrite_list: function (web) {
			var filename = '/www/server/panel/vhost/rewrite/' + web.name + '.conf';
			bt.site.get_rewrite_list(web.name, function (rdata) {
				var arrs = [],
					webserver = bt.get_cookie('serverType');
				if (webserver == 'apache' || webserver == 'openlitespeed') filename = rdata.sitePath + '/.htaccess';
				if (webserver == 'openlitespeed') webserver = 'apache';
				for (var i = 0; i < rdata.rewrite.length; i++)
					arrs.push({
						title: rdata.rewrite[i],
						value: rdata.rewrite[i],
					});
				var datas = [
					{
						name: 'rewrite',
						type: 'select',
						width: '130px',
						items: arrs,
						callback: function (obj) {
							if (bt.os == 'Linux') {
								var spath = filename;
								if (obj.val() != lan.site.rewritename) spath = '/www/server/panel/rewrite/' + (webserver == 'openlitespeed' ? 'apache' : webserver) + '/' + obj.val() + '.conf';
								bt.files.get_file_body(spath, function (ret) {
									if (ret.status == false) {
										layer.msg(ret.msg, { icon: 2 });
										return false;
									}
									aceEditor.ACE.setValue(ret.data);
									aceEditor.ACE.moveCursorTo(0, 0);
									aceEditor.path = spath;
								});
							}
						},
					},
					{ items: [{ name: 'config', type: 'div', value: rdata.data, widht: '340px', height: '200px' }] },
					{
						items: [
							{
								name: 'btn_save',
								text: lan.site.save,
								type: 'button',
								callback: function (ldata) {
									// bt.files.set_file_body(filename, editor.getValue(), 'utf-8', function(ret) {
									//     if (ret.status) site.reload(4)
									//     bt.msg(ret);
									// })
									aceEditor.path = filename;
									bt.saveEditor(aceEditor);
								},
							},
							{
								name: 'btn_save_to',
								text: lan.site.save_as_template,
								type: 'button',
								callback: function (ldata) {
									var temps = {
										title: lan.site.save_rewrite_temp,
										area: '330px',
										list: [
											{
												title: lan.site.template_name,
												placeholder: lan.site.template_name,
												width: '160px',
												name: 'tempname',
											},
										],
										btns: [
											{ title: lan.site.turn_off, name: 'close' },
											{
												title: lan.site.submit,
												name: 'submit',
												css: 'btn-success',
												callback: function (rdata, load, callback) {
													var name = rdata.tempname;
													if (name === '') return layer.msg('The template name cannot be empty!', { icon: 2 });
													var isSameName = false;
													for (var i = 0; i < arrs.length; i++) {
														if (arrs[i].value == name) {
															isSameName = true;
															break;
														}
													}
													var save_to = function () {
														bt.site.set_rewrite_tel(name, aceEditor.ACE.getValue(), function (rRet) {
															if (rRet.status) {
																load.close();
																site.reload(4);
															}
															bt.msg(rRet);
														});
													};
													if (isSameName) {
														return layer.msg('The template name already exists, please re-enter the template name!', { icon: 2 });
													} else {
														save_to();
													}
												},
											},
										],
									};
									bt.render_form(temps);
								},
							},
						],
					},
				];
				var _html = $("<div class='webedit-box soft-man-con'></div>");
				var clicks = [];
				for (var i = 0; i < datas.length; i++) {
					var _form_data = bt.render_form_line(datas[i]);
					_html.append(_form_data.html);
					var _other =
						bt.os == 'Linux' && i == 0
							? '<span>' + lan.site.rewrite_change_tools + '：<a href="https://www.bt.cn/Tools" target="_blank" style="color:#20a53a">' + lan.site.ap_change_ng + '</a></span>'
							: '';
					_html.find('.info-r').append(_other);
					clicks = clicks.concat(_form_data.clicks);
				}
				_html.append(bt.render_help([lan.site.rewrite_tips_1, lan.site.rewrite_tips_2, lan.site.edit_rewrite]));
				$('#webedit-con').append(_html);
				bt.render_clicks(clicks);

				// $('textarea.config').attr('id', 'config_rewrite');
				// var editor = CodeMirror.fromTextArea(document.getElementById("config_rewrite"), {
				//     extraKeys: { "Ctrl-Space": "autocomplete" },
				//     lineNumbers: true,
				//     matchBrackets: true,
				// });

				// $(".CodeMirror-scroll").css({ "height": "340px", "margin": 0, "padding": 0 });
				// $(".soft-man-con .CodeMirror").css({ "height": "342px" });
				// setTimeout(function() {
				//     editor.refresh();
				// }, 250);
				$('div.config').attr('id', 'config_rewrite').css({ height: '360px', width: '540px' });
				var aceEditor = bt.aceEditor({ el: 'config_rewrite', content: rdata.data });

				$('select.rewrite').trigger('change');
			});
		},
		set_default_index: function (web) {
			bt.site.get_index(web.id, function (rdata) {
				rdata = rdata.replace(new RegExp(/(,)/g), '\n');
				var data = {
					items: [
						{ name: 'Dindex', height: '230px', width: '50%', type: 'textarea', value: rdata },
						{
							name: 'btn_submit',
							text: lan.site.add,
							type: 'button',
							callback: function (ddata) {
								var Dindex = ddata.Dindex.replace(new RegExp(/(\n)/g), ',');
								bt.site.set_index(web.id, Dindex, function (ret) {
									if (!ret.status) {
										bt.msg(ret);
										return;
									}

									site.reload(5);
								});
							},
						},
					],
				};
				var _form_data = bt.render_form_line(data);
				var _html = $(_form_data.html);
				_html.append(bt.render_help([lan.site.default_doc_help]));
				$('#webedit-con').append(_html);
				$('.btn_submit').addClass('pull-right').css('margin', '90px 100px 0 0');
				bt.render_clicks(_form_data.clicks);
			});
		},
		set_config: function (web) {
			var con =
				'<p style="color: #666; margin-bottom: 7px">Tips：Ctrl+F Search keywords，Ctrl+S Save，Ctrl+H Search and replace</p><div class="bt-input-text ace_config_editor_scroll" style="height: 400px; line-height:18px;" id="siteConfigBody"></div>\
      <button id="OnlineEditFileBtn" class="btn btn-success btn-sm" style="margin-top:10px;">Save</button>\
      <ul class="help-info-text c7">\
                  <li>This is primary configuration file of the site.</li>\
                  <li>Do not modify it at will if you do not know configuration rules.</li>\
      </ul>';
			$('#webedit-con').html(con);
			var webserve = bt.get_cookie('serverType'),
				config = bt.aceEditor({
					el: 'siteConfigBody',
					path: '/www/server/panel/vhost/' + (webserve == 'openlitespeed' ? webserve + '/detail' : webserve) + '/' + web.name + '.conf',
				});
			$('#OnlineEditFileBtn').click(function (e) {
				bt.saveEditor(config);
			});
		},
		set_php_version: function (web) {
			bt.site.get_site_phpversion(web.name, function (sdata) {
				if (sdata.status === false) {
					bt.msg(sdata);
					return;
				}
				bt.site.get_all_phpversion(function (vdata) {
					var versions = [];
					for (var j = vdata.length - 1; j >= 0; j--) {
						var o = vdata[j];
						o.value = o.version;
						o.title = o.name;
						versions.push(o);
					}

					// var data = {
					//     items: [
					//         {
					//             title: 'PHP版本',
					//             name: 'versions',
					//             value: sdata.phpversion,
					//             type: 'select',
					//             items: versions ,
					//             ps:'<input class="bt-input-text other-version" style="margin-right: 10px;width:300px;color: #000;" type="text" value="'+sdata.php_other+'" placeholder="连接配置，如：1.1.1.1:9001或unix:/tmp/php.sock" />'
					//         },
					//         {
					//             text: '切换',
					//             name: 'btn_change_phpversion',
					//             type: 'button',
					//             callback: function(pdata) {
					//                 var other = $('.other-version').val();
					//                 if(pdata.versions == 'other' && other == ''){
					//                     layer.msg('自定义PHP版本时，PHP连接配置不能为空');
					//                     $('.other-version').focus();
					//                     return;
					//                 }
					//                 bt.site.set_phpversion(web.name, pdata.versions, other, function(ret) {
					//                     if (ret.status) {
					//                         var versions = $('[name="versions"]').val();
					//                         versions = versions.slice(0, versions.length - 1) + '.' + versions.slice(-1);
					//                         if (versions == '0.0') versions = '静态';
					//                         site_table.$refresh_table_list(true);
					//                         site.reload()
					//                         setTimeout(function() {
					//                             bt.msg(ret);
					//                         }, 1000);
					//                     }else{
					//                         bt.msg(ret);
					//                     }

					//                 })
					//             }
					//         }
					//     ]
					// }
					// var _form_data = bt.render_form_line(data);
					// var _html = $(_form_data.html);
					// _html.append(bt.render_help([lan.site.switch_php_help1, lan.site.switch_php_help2, lan.site.switch_php_help3]));
					// $('#webedit-con').append(_html);
					// bt.render_clicks(_form_data.clicks);
					// $('#webedit-con').append('<div class="user_pw_tit" style="margin-top: 2px;padding-top: 11px;border-top: #ccc 1px dashed;"><span class="tit">' + lan.site.session_off + '</span><span class="btswitch-p ml5" style="margin-bottom: 0;display: inline-block;vertical-align: middle;"><input class="btswitch btswitch-ios" id="session_switch" type="checkbox"><label class="btswitch-btn session-btn" for="session_switch" ></label></span></div><div class="user_pw" style="margin-top: 10px; display: block;"></div>' + bt.render_help([lan.site.independent_storage]));

					// function get_session_status() {
					//     var loading = bt.load('Getting session status...');
					//     bt.send('get_php_session_path', 'config/get_php_session_path', { id: web.id }, function(tdata) {
					//         loading.close();
					//         $('#session_switch').prop("checked", tdata);
					//     })
					// };
					// get_session_status()
					// $('#session_switch').click(function() {
					//     var val = $(this).prop('checked');
					//     bt.send('set_php_session_path', 'config/set_php_session_path', { id: web.id, act: val ? 1 : 0 }, function(rdata) {
					//         get_session_status();
					//         bt.msg(rdata)
					//     });
					// })

					var data = {
						items: [
							{
								title: 'PHP version',
								name: 'versions',
								value: sdata.phpversion,
								type: 'select',
								items: versions,
								ps:
									'<input class="bt-input-text other-version" style="margin-right: 10px;width:300px;color: #000;" type="text" value="' +
									sdata.php_other +
									'" placeholder="e.g:1.1.1.1:9001 or unix:/tmp/php.sock" />',
							},
							{
								text: 'Switch',
								name: 'btn_change_phpversion',
								type: 'button',
								callback: function (pdata) {
									var other = $('.other-version').val();
									if (pdata.versions == 'other' && other == '') {
										layer.msg('When customizing the PHP version, the PHP connection configuration cannot be empty');
										$('.other-version').focus();
										return;
									}
									bt.site.set_phpversion(web.name, pdata.versions, other, function (ret) {
										if (ret.status) {
											var versions = $('[name="versions"]').val();
											versions = versions.slice(0, versions.length - 1) + '.' + versions.slice(-1);
											if (versions == '0.0') versions = 'Static';
											site_table.$refresh_table_list(true);
											site.reload();
											setTimeout(function () {
												bt.msg(ret);
											}, 1000);
										} else {
											bt.msg(ret);
										}
									});
								},
							},
						],
					};
					var _form_data = bt.render_form_line(data);
					var _html = $(_form_data.html);
					_html.append(
						bt.render_help([
							'Select the version according to your program requirements',
							'Try not to use PHP5.2 unless you have to, as this can reduce your server security',
							'PHP7 does not support the MySQL extension. The default installation is mysqli and mysql-pdo',
							'[Customize] You can customize the PHP connection information by selecting the available PHP connection configuration',
							'[Customize] Currently only support NGINX',
							'Support TCP or UNIX configuration. Example: 192.168.1.25:9001 or unix:/tmp/php8.sock',
						])
					);
					$('#webedit-con').append(_html);
					bt.render_clicks(_form_data.clicks);
					if (sdata.phpversion != 'other') {
						var tips = bt.render_help([
							'When enabled, session files will be stored in a separate folder, not in a common storage location with other sites',
							'Do not enable this option if you are saving sessions to caches such as memcache/redis in your PHP configuration',
						]);

						$('#webedit-con').append(
							'\
												<div class="user_pw_tit" style="display: flex; items-align: center; margin-top: 2px;padding-top: 11px;border-top: #ccc 1px dashed;">\
													<span class="tit mr10" style="padding-top: 1px;">' +
								lan.site.session_off +
								'</span>\
													<span class="btswitch-p"style="display: inline-flex;">\
														<input class="btswitch btswitch-ios" id="session_switch" type="checkbox">\
														<label class="btswitch-btn session-btn" for="session_switch" ></label>\
													</span>\
												</div>\
												<div class="user_pw" style="margin-top: 10px; display: block;"></div>' +
								tips
						);
					}
					if (sdata.phpversion != 'other') {
						$('.other-version').hide();
					}
					setTimeout(function () {
						$('select[name="versions"]').change(function () {
							var phpversion = $(this).val();
							// console.log(phpversion);
							if (phpversion == 'other') {
								$('.other-version').show();
							} else {
								$('.other-version').hide();
							}
						});
					}, 500);

					function get_session_status() {
						var loading = bt.load('Please wait while getting session status');
						bt.send('get_php_session_path', 'config/get_php_session_path', { id: web.id }, function (tdata) {
							loading.close();
							$('#session_switch').prop('checked', tdata);
						});
					}
					get_session_status();
					$('#session_switch').click(function () {
						var val = $(this).prop('checked');
						bt.send(
							'set_php_session_path',
							'config/set_php_session_path',
							{
								id: web.id,
								act: val ? 1 : 0,
							},
							function (rdata) {
								bt.msg(rdata);
							}
						);
						setTimeout(function () {
							get_session_status();
						}, 500);
					});
				});
			});
		},
		set_wp_config: function (web) {
			var loadup = bt.load('Getting Wordpress information, please wait...');
			bt.send('is_update', 'site/is_update', { s_id: web.id }, function (rdata) {
				loadup.close();
				var loadin = bt.load('Getting wordpress account information, please wait...');
				bt.send('get_wp_username', 'site/get_wp_username', { s_id: web.id }, function (wlist) {
					loadin.close();
					var robj = $('#webedit-con');

					if (wlist.status === false) {
						wlist.time = 0;
						wlist.closeBtn = 2;
						bt.msg(wlist);
						var data = {
							items: [
								{
									title: 'Database name',
									name: 'database',
									value: '',
									type: 'input',
									width: '250px',
									placeholder: 'Please enter the database name',
								},
								{
									text: 'Set',
									name: 'btn_change_database',
									type: 'button',
									callback: function (pdata) {
										if (pdata.database == '') {
											return layer.msg('The database name cannot be empty', { icon: 2 });
										}
										var param = {
											site_id: web.id,
											db_name: pdata.database,
										};
										var load = bt.load('Setting Database name, please wait...');
										bt.send('reset_wp_db', 'site/reset_wp_db', param, function (res) {
											load.close();
											bt.msg(res);
											if (res.status) {
												setTimeout(function () {
													robj.html('');
													site.edit.set_wp_config(web);
												}, 1500);
											}
										});
									},
								},
							],
						};
						var _form_data = bt.render_form_line(data);
						var _html = $(_form_data.html);
						_html.append(bt.render_help(['Please enter the database name for this wordpress website']));
						robj.append(_html);
						bt.render_clicks(_form_data.clicks);
						return;
					}

					var _html = $('<div class="webedit-box soft-man-con"></div>'),
						user_array = [],
						clicks = [];

					$.each(wlist.msg, function (index, item) {
						user_array.push({ title: item, value: item });
					});
					var datas = [
						{
							title: 'WP Version',
							items: [
								{
									name: 'wp_version',
									type: 'html',
									html: rdata['msg']['update']
										? '<span class="c7 mr10">The current version is: ' +
										  rdata['msg']['local_v'] +
										  '</span><button class="btn btn-success btn-sm mr5 ml5 update_wp_version">upgrade to ' +
										  rdata['msg']['online_v'] +
										  '</button>'
										: '<span class="c7">The latest version</span>',
								},
							],
						},
						{
							title: 'Cache',
							items: [
								{
									type: 'checkbox',
									name: 'cache_switch',
									text: ' Open cache',
									value: web.cache_status,
									callback: function (sdata) {
										var loads = bt.load((sdata.cache_switch ? 'Turning on' : 'Turining off') + ' [ ' + web.name + ' ] cache, please wait...');
										bt.send('set_fastcgi_cache', 'site/set_fastcgi_cache', { version: web.php_version, sitename: web.name, act: sdata.cache_switch ? 'enable' : 'disable' }, function (res) {
											loads.close();
											bt.msg(res);
											if (res.status) {
												site.php_table_view();
												web.cache_status = sdata.cache_switch;
											}
										});
									},
								},
								{
									name: 'remove_cache',
									text: 'Purge all cache',
									type: 'button',
									callback: function (sdata) {
										var loadC = bt.load('Clearing all caches, please wait...');
										bt.send('purge_all_cache', 'site/purge_all_cache', { s_id: web.id }, function (res) {
											loadC.close();
											bt.msg(res);
										});
									},
								},
							],
						},
						{
							title: 'Reset password',
							items: [
								{
									name: 'user',
									type: 'select',
									items: user_array,
									width: '200px',
								},
								{
									title: '',
									name: 'new_pass',
									placeholder: 'Please enter a new password',
									width: '200px',
								},
								{
									name: 'submit_pw',
									text: 'Save password',
									type: 'button',
									callback: function (sdata) {
										var loads = bt.load('Resetting password, please wait...');
										bt.send('reset_wp_password', 'site/reset_wp_password', { s_id: web.id, user: sdata.user, new_pass: sdata.new_pass }, function (res) {
											loads.close();
											bt.msg(res);
										});
									},
								},
							],
						},
					];
					for (var i = 0; i < datas.length; i++) {
						var _form_data = bt.render_form_line(datas[i]);
						_html.append(_form_data.html);
						clicks = clicks.concat(_form_data.clicks);
					}
					_html.find('input[type="checkbox"]').parent().addClass('label-input-group');
					_html.find('button[name="submit_pw"]').css('margin', '15px 0');
					robj.append(_html);
					bt.render_clicks(clicks);

					//wp版本更新
					$('.update_wp_version').click(function () {
						var load_wp = bt.load('Updating Wordpress version, please wait...');
						bt.send('update_wp', 'site/update_wp', { s_id: web.id, version: rdata['msg']['online_v'] }, function (res) {
							load_wp.close();
							bt.msg(res);
							if (res.status) $('.bt-w-menu.site-menu p.bgw').click();
						});
					});
				});
			});
		},
		templet_301: function (sitename, id, types, obj) {
			if (types) {
				obj = {
					redirectname: new Date().valueOf(),
					tourl: 'http://',
					redirectdomain: [],
					redirectpath: '',
					redirecttype: '',
					type: 1,
					domainorpath: 'domain',
					holdpath: 1,
				};
			}
			var helps = [lan.site.redirect_tips1, lan.site.redirect_tips2, lan.site.redirect_tips3, lan.site.redirect_tips4, lan.site.redirect_tips5, lan.site.redirect_tips6];
			bt.site.get_domains(id, function (rdata) {
				var domain_html = '';
				for (var i = 0; i < rdata.length; i++) {
					domain_html += '<option value="' + rdata[i].name + '">' + rdata[i].name + '</option>';
				}
				var form_redirect = bt.open({
					type: 1,
					skin: 'demo-class',
					area: '650px',
					title: types ? lan.site.create_redirect : lan.site.modify_redirect + '[' + obj.redirectname + ']',
					closeBtn: 2,
					shift: 5,
					shadeClose: false,
					content:
						"<form id='form_redirect' class='divtable pd20' style='padding-bottom: 60px'>" +
						"<div class='line' style='overflow:hidden;height: 40px;'>" +
						"<span class='tname' style='position: relative;top: -5px;'>" +
						lan.site.open_redirect +
						'</span>' +
						"<div class='info-r  ml0 mt5' >" +
						"<input class='btswitch btswitch-ios' id='type' type='checkbox' name='type' " +
						(obj.type == 1 ? 'checked="checked"' : '') +
						" /><label class='btswitch-btn phpmyadmin-btn' for='type' style='float:left'></label>" +
						"<div style='display: inline-block;'>" +
						"<span class='tname' style='margin-left:51px;position: relative;top: -5px; width:150px;'>" +
						lan.site.reserve_url +
						'</span>' +
						"<input class='btswitch btswitch-ios' id='holdpath' type='checkbox' name='holdpath' " +
						(obj.holdpath == 1 ? 'checked="checked"' : '') +
						" /><label class='btswitch-btn phpmyadmin-btn' for='holdpath' style='float:left'></label>" +
						'</div>' +
						'</div>' +
						'</div>' +
						"<div class='line' style='clear:both;display:none;'>" +
						"<span class='tname'>" +
						lan.site.redirect_name +
						'</span>' +
						"<div class='info-r  ml0'><input name='redirectname' class='bt-input-text mr5' " +
						(types ? '' : 'disabled="disabled"') +
						" type='text' style='width:300px' value='" +
						obj.redirectname +
						"'></div>" +
						'</div>' +
						"<div class='line' style='clear:both;'>" +
						"<span class='tname'>" +
						lan.site.redirect_type +
						'</span>' +
						"<div class='info-r  ml0'>" +
						"<select class='bt-input-text mr5' name='domainorpath' style='width:100px'><option value='domain' " +
						(obj.domainorpath == 'domain' ? 'selected ="selected"' : '') +
						'>' +
						lan.site.domain +
						"</option><option value='path'  " +
						(obj.domainorpath == 'path' ? 'selected ="selected"' : '') +
						'>' +
						lan.site.path +
						'</option></select>' +
						"<span class='mlr15'>" +
						lan.site.redirect_mode +
						'</span>' +
						"<select class='bt-input-text ml10' name='redirecttype' style='width:100px'><option value='301' " +
						(obj.redirecttype == '301' ? 'selected ="selected"' : '') +
						" >301</option><option value='302' " +
						(obj.redirecttype == '302' ? 'selected ="selected"' : '') +
						'>302</option></select></div>' +
						'</div>' +
						"<div class='line redirectdomain' style='display:" +
						(obj.domainorpath == 'domain' ? 'block' : 'none') +
						"'>" +
						"<span class='tname'>" +
						lan.site.redirect_domain +
						'</span>' +
						"<div class='info-r  ml0' style='height: 35px;'>" +
						"<select id='usertype' name='redirectdomain' data-actions-box='true' class='selectpicker show-tick form-control' multiple data-live-search='false'>" +
						domain_html +
						'</select>' +
						'</div>' +
						"<span class='tname'>" +
						lan.site.target_url +
						'</span>' +
						"<div class='info-r  ml0'>" +
						"<input  name='tourl' class='bt-input-text mr5' type='text' style='width:200px;padding-left: 9px;' value='" +
						obj.tourl +
						"'>" +
						'</div>' +
						'</div>' +
						"<div class='line redirectpath' style='display:" +
						(obj.domainorpath == 'path' ? 'block' : 'none') +
						"'>" +
						"<span class='tname'>" +
						lan.site.redirect_path +
						'</span>' +
						"<div class='info-r  ml0'>" +
						"<input  name='redirectpath' class='bt-input-text mr5' type='text' style='width:200px;float: left;margin-right:0px' value='" +
						obj.redirectpath +
						"'>" +
						"<span class='tname' style='width:90px'>" +
						lan.site.target_url +
						'</span>' +
						"<input  name='tourl1' class='bt-input-text mr5' type='text' style='width:200px' value='" +
						obj.tourl +
						"'>" +
						'</div>' +
						'</div>' +
						"<ul class='help-info-text c7'>" +
						bt.render_help(helps) +
						'</ul>' +
						"<div class='bt-form-submit-btn'><button type='button' class='btn btn-sm btn-danger btn-colse-prosy'>" +
						lan.site.no +
						"</button><button type='button' class='btn btn-sm btn-success btn-submit-redirect'>" +
						(types ? ' ' + lan.site.submit : lan.site.save) +
						'</button></div>' +
						'</form>',
				});
				setTimeout(function () {
					$('.selectpicker').selectpicker({
						noneSelectedText: lan.site.choose_domain,
						selectAllText: lan.site.choose_all,
						deselectAllText: lan.site.cancel_all,
					});
					$('.selectpicker').selectpicker('val', obj.redirectdomain);
					$('#form_redirect').parent().css('overflow', 'inherit');
					$('[name="domainorpath"]').change(function () {
						if ($(this).val() == 'path') {
							$('.redirectpath').show();
							$('.redirectdomain').hide();
							$('.selectpicker').selectpicker('val', []);
						} else {
							$('.redirectpath').hide();
							$('.redirectdomain').show();
							$('[name="redirectpath"]').val('');
						}
					});
					$('.btn-colse-prosy').click(function () {
						form_redirect.close();
					});
					$('.btn-submit-redirect').click(function () {
						var type = $('[name="type"]').prop('checked') ? 1 : 0;
						var holdpath = $('[name="holdpath"]').prop('checked') ? 1 : 0;
						var redirectname = $('[name="redirectname"]').val();
						var redirecttype = $('[name="redirecttype"]').val();
						var domainorpath = $('[name="domainorpath"]').val();
						var redirectpath = $('[name="redirectpath"]').val();
						var redirectdomain = JSON.stringify($('.selectpicker').val() || []);
						var tourl = $(domainorpath == 'path' ? '[name="tourl1"]' : '[name="tourl"]').val();
						if (!types) {
							bt.site.modify_redirect(
								{
									type: type,
									sitename: sitename,
									holdpath: holdpath,
									redirectname: redirectname,
									redirecttype: redirecttype,
									domainorpath: domainorpath,
									redirectpath: redirectpath,
									redirectdomain: redirectdomain,
									tourl: tourl,
								},
								function (rdata) {
									if (rdata.status) {
										form_redirect.close();
										site.reload(11);
									}
									bt.msg(rdata);
								}
							);
						} else {
							bt.site.create_redirect(
								{
									type: type,
									sitename: sitename,
									holdpath: holdpath,
									redirectname: redirectname,
									redirecttype: redirecttype,
									domainorpath: domainorpath,
									redirectpath: redirectpath,
									redirectdomain: redirectdomain,
									tourl: tourl,
								},
								function (rdata) {
									if (rdata.status) {
										form_redirect.close();
										site.reload(11);
									}
									bt.msg(rdata);
								}
							);
						}
					});
				}, 100);
			});
		},
		template_Dir: function (id, type, obj) {
			if (type) {
				obj = { name: '', sitedir: '', username: '', password: '' };
			} else {
				obj = { name: obj.name, sitedir: obj.site_dir, username: '', password: '' };
			}
			var form_directory = bt.open({
				type: 1,
				skin: 'demo-class',
				area: '475px',
				title: type ? 'Add limit access' : 'Edit limit access',
				closeBtn: 2,
				shift: 5,
				shadeClose: false,
				content:
					"<form id='form_dir' class='divtable pd15' style='padding: 20px 0 60px 0'>" +
					"<div class='line'>" +
					"<span class='tname'>" +
					lan.bt.task_name +
					'</span>' +
					"<div class='info-r ml0'><input name='dir_name' class='bt-input-text mr10' type='text' style='width:270px' value='" +
					obj.name +
					"'>" +
					'</div></div>' +
					"<div class='line'>" +
					"<span class='tname'>Path</span>" +
					"<div class='info-r ml0'><input name='dir_sitedir' placeholder='Enter the path: /text/，/test/api' class='bt-input-text mr10' type='text' style='width:270px' value='" +
					obj.sitedir +
					"'>" +
					'</div></div>' +
					"<div class='line'>" +
					"<span class='tname'>" +
					lan.bt.panel_user +
					'</span>' +
					"<div class='info-r ml0'><input name='dir_username' AUTOCOMPLETE='off' class='bt-input-text mr10' type='text' style='width:270px' value='" +
					obj.username +
					"'>" +
					'</div></div>' +
					"<div class='line'>" +
					"<span class='tname'>" +
					lan.bt.panel_pass +
					'</span>' +
					"<div class='info-r ml0'><input name='dir_password' AUTOCOMPLETE='off' class='bt-input-text mr10' type='text' style='width:270px' value='" +
					obj.password +
					"'>" +
					'</div></div>' +
					"<ul class='help-info-text c7 plr20'>" +
					'<li>After the path is protected, you need to enter the account password to access it.</li>' +
					'<li>For example, if I set the protection directory /test/ , then I need to enter the account password to access http://aaa.com/test/</li>' +
					'</ul>' +
					"<div class='bt-form-submit-btn'><button type='button' class='btn btn-sm btn-danger btn-colse-guard'>" +
					lan.site.turn_off +
					"</button><button type='button' class='btn btn-sm btn-success btn-submit-guard'>" +
					(type ? ' ' + lan.site.submit : lan.site.save) +
					'</button></div></form>',
			});
			$('.btn-colse-guard').click(function () {
				form_directory.close();
			});
			$('.btn-submit-guard').click(function () {
				var guardData = {};
				guardData['id'] = id;
				guardData['name'] = $('input[name="dir_name"]').val();
				guardData['site_dir'] = $('input[name="dir_sitedir"]').val();
				guardData['username'] = $('input[name="dir_username"]').val();
				guardData['password'] = $('input[name="dir_password"]').val();
				if (type) {
					bt.site.create_dir_guard(guardData, function (rdata) {
						if (rdata.status) {
							form_directory.close();
							site.reload();
						}
						bt.msg(rdata);
					});
				} else {
					bt.site.edit_dir_account(guardData, function (rdata) {
						if (rdata.status) {
							form_directory.close();
							site.reload();
						}
						bt.msg(rdata);
					});
				}
			});
			setTimeout(function () {
				if (!type) {
					$('input[name="dir_name"]').attr('disabled', 'disabled');
					$('input[name="dir_sitedir"]').attr('disabled', 'disabled');
				}
			}, 500);
		},
		template_php: function (website, obj) {
			var _type = 'add',
				_name = '',
				_bggrey = '';
			if (obj == undefined) {
				obj = { name: '', suffix: 'php|jsp', dir: '' };
			} else {
				obj = { name: obj.name, suffix: obj.suffix, dir: obj.dir };
				_type = 'edit';
				_name = ' readonly';
				_bggrey = 'background: #eee;';
			}
			var form_directory = bt.open({
				type: 1,
				area: '440px',
				title: 'Deny access',
				closeBtn: 2,
				btn: ['Save', 'Cancel'],
				content:
					"<form class='mt10 php_deny'>" +
					"<div class='line'>" +
					"<span class='tname' style='width: 100px;'>Name</span>" +
					"<div class='info-r ml0' style='margin-left: 100px;'><input name='deny_name' placeholder='The rule name' " +
					_name +
					" class='bt-input-text mr10' type='text' style='width:270px;" +
					_bggrey +
					"' value='" +
					obj.name +
					"'>" +
					'</div></div>' +
					"<div class='line'>" +
					"<span class='tname' style='width: 100px;'>Suffix</span>" +
					"<div class='info-r ml0' style='margin-left: 100px;'><input name='suffix' placeholder='Suffixes that are not allowed' class='bt-input-text mr10' type='text' style='width:270px' value='" +
					obj.suffix +
					"'>" +
					'</div></div>' +
					"<div class='line'>" +
					"<span class='tname' style='width: 100px;'>Path</span>" +
					"<div class='info-r ml0' style='margin-left: 100px;'><input name='dir' placeholder='Quote rules in this directory. e.g: /a/' class='bt-input-text mr10' type='text' style='width:270px' value='" +
					obj.dir +
					"'>" +
					'</div></div></form>' +
					"<ul class='help-info-text c7 plr20'>" +
					'<li>Name:The rule name.</li>' +
					"<li>Suffix: Indicates the suffix that is not allowed to access, if there are more than one, separate with'|'</li>" +
					'<li>Path: Quote rules in this directory. e.g: /a/ </li>' +
					'<li>For Example, if you want to deny http://test.com/a/index.php</li>' +
					'<li>Please fill in [ /a/ ]' +
					'</ul>',
				yes: function () {
					var dent_data = $('.php_deny').serializeObject();
					dent_data.act = _type;
					dent_data.website = website;
					var loading = bt.load();
					bt.site.edit_php_deny(dent_data, function (rdata) {
						loading.close();
						if (rdata.status) {
							form_directory.close();
							site.reload();
							$('#set_dirguard .tab-nav span:eq(1)').click();
						}
						bt.msg(rdata);
					});
				},
			});
		},
		del_php_deny: function (website, deny_name, callback) {
			layer.confirm(
				'Are you sure to delete [ ' + deny_name + ' ] this deny?',
				{
					icon: 0,
					closeBtn: 2,
					title: 'Delete deny',
				},
				function (index) {
					bt.site.del_php_deny({ website: website, deny_name: deny_name }, function (rdata) {
						layer.close(index);
						if (callback) callback(rdata);
					});
				}
			);
		},
		set_301_old: function (web) {
			bt.site.get_domains(web.id, function (rdata) {
				var domains = [{ title: lan.site.site, value: 'all' }];
				for (var i = 0; i < rdata.length; i++) domains.push({ title: rdata[i].name, value: rdata[i].name });

				bt.site.get_site_301(web.name, function (pdata) {
					var _val = pdata.src == '' ? 'all' : pdata.src;
					var datas = [
						{
							title: lan.site.access_domain,
							width: '360px',
							name: 'domains',
							value: _val,
							disabled: pdata.status,
							type: 'select',
							items: domains,
						},
						{ title: lan.site.target_url, width: '360px', name: 'toUrl', value: pdata.url },
						{
							title: ' ',
							text: lan.site.enable_301,
							value: pdata.status,
							name: 'status',
							class: 'label-input-group',
							type: 'checkbox',
							callback: function (sdata) {
								bt.site.set_site_301(web.name, sdata.domains, sdata.toUrl, sdata.status ? '1' : '0', function (ret) {
									if (ret.status) site.reload(10);
									bt.msg(ret);
								});
							},
						},
					];
					var robj = $('#webedit-con');
					for (var i = 0; i < datas.length; i++) {
						var _form_data = bt.render_form_line(datas[i]);
						robj.append(_form_data.html);
						bt.render_clicks(_form_data.clicks);
					}
					robj.append(bt.render_help([lan.site.to301_help_1, lan.site.to301_help_2]));
				});
			});
		},
		set_301: function (web) {
			$('#webedit-con').html('<div id="redirect_list"></div>');
			bt_tools.table({
				el: '#redirect_list',
				url: '/site?action=GetRedirectList',
				param: { sitename: web.name },
				dataFilter: function (res) {
					return { data: res };
				},
				column: [
					{ type: 'checkbox', width: 20 },
					{
						fid: 'sitename',
						title: lan.site.redirect_type,
						type: 'text',
						template: function (row) {
							if (row.domainorpath == 'path') {
								conter = row.redirectpath;
							} else {
								conter = row.redirectdomain ? row.redirectdomain.join('、') : lan.site.empty;
							}
							return '<span class="limit-text-length" style="max-width:125px;" title="' + conter + '">' + conter + '</span>';
						},
					},
					{ fid: 'redirecttype', title: lan.site.redirect_mode, type: 'text' },
					{
						fid: 'holdpath',
						title: lan.site.reserve_url,
						config: {
							icon: false,
							list: [
								[1, lan.site.turn_on, 'bt_success'],
								[0, lan.site.turn_off, 'bt_danger'],
							],
						},
						type: 'status',
						event: function (row, index, ev, key, that) {
							row.holdpath = row.holdpath == 0 ? 1 : 0;
							row.redirectdomain = JSON.stringify(row['redirectdomain']);
							bt.site.modify_redirect(row, function (res) {
								row.redirectdomain = JSON.parse(row['redirectdomain']);
								that.$modify_row_data({ holdpath: row.holdpath });
								bt.msg(res);
							});
						},
					},
					{
						fid: 'type',
						title: lan.site.status,
						config: {
							icon: true,
							list: [
								[1, lan.site.running_text, 'bt_success', 'glyphicon-play'],
								[0, lan.site.already_stop, 'bt_danger', 'glyphicon-pause'],
							],
						},
						type: 'status',
						event: function (row, index, ev, key, that) {
							row.type = row.type == 0 ? 1 : 0;
							row.redirectdomain = JSON.stringify(row['redirectdomain']);
							bt.site.modify_redirect(row, function (res) {
								row.redirectdomain = JSON.parse(row['redirectdomain']);
								that.$modify_row_data({ status: row.type });
								bt.msg(res);
							});
						},
					},
					{
						title: lan.site.operate,
						width: 129,
						type: 'group',
						align: 'right',
						group: [
							{
								title: 'Conf',
								event: function (row, index, ev, key, that) {
									bt.site.get_redirect_config(
										{
											sitename: web.name,
											redirectname: row.redirectname,
											webserver: bt.get_cookie('serverType'),
										},
										function (rdata) {
											if (typeof rdata == 'object' && rdata.constructor == Array) {
												if (!rdata[0].status) bt.msg(rdata);
											} else {
												if (!rdata.status) bt.msg(rdata);
											}
											var datas = [
												{
													items: [
														{
															name: 'redirect_configs',
															type: 'textarea',
															value: rdata[0].data,
															widht: '340px',
															height: '200px',
														},
													],
												},
												{
													name: 'btn_config_submit',
													text: 'Save',
													type: 'button',
													callback: function (ddata) {
														bt.site.save_redirect_config(
															{
																path: rdata[1],
																data: editor.getValue(),
																encoding: rdata[0].encoding,
															},
															function (ret) {
																if (ret.status) {
																	site.reload(11);
																	redirect_config.close();
																}
																bt.msg(ret);
															}
														);
													},
												},
											];
											redirect_config = bt.open({
												type: 1,
												area: ['550px', '550px'],
												title: 'Edit profile [' + row.redirectname + ']',
												closeBtn: 2,
												shift: 0,
												content: "<div class='bt-form'><div id='redirect_config_con' class='pd15'></div></div>",
											});
											var robj = $('#redirect_config_con');
											for (var i = 0; i < datas.length; i++) {
												var _form_data = bt.render_form_line(datas[i]);
												robj.append(_form_data.html);
												bt.render_clicks(_form_data.clicks);
											}
											robj.append(bt.render_help(['This is the configuration file of the load balancing. Not modify if you do not understand the configuration rules.']));
											$('textarea.redirect_configs').attr('id', 'configBody');
											var editor = CodeMirror.fromTextArea(document.getElementById('configBody'), {
												extraKeys: { 'Ctrl-Space': 'autocomplete' },
												lineNumbers: true,
												matchBrackets: true,
											});
											$('.CodeMirror-scroll').css({ height: '350px', margin: 0, padding: 0 });
											setTimeout(function () {
												editor.refresh();
											}, 250);
										}
									);
								},
							},
							{
								title: lan.site.edit,
								event: function (row, index, ev, key, that) {
									site.edit.templet_301(web.name, web.id, false, row);
								},
							},
							{
								title: lan.site.del,
								event: function (row, index, ev, key, that) {
									bt.site.remove_redirect(web.name, row.redirectname, function (rdata) {
										if (rdata.status) that.$delete_table_row(index);
									});
								},
							},
						],
					},
				],
				tootls: [
					{
						//按钮组
						type: 'group',
						positon: ['left', 'top'],
						list: [
							{
								title: 'Add redirection',
								active: true,
								event: function (ev) {
									site.edit.templet_301(web.name, web.id, true);
								},
							},
						],
					},
					{
						//批量操作
						type: 'batch',
						positon: ['left', 'bottom'],
						config: {
							title: ' delete',
							url: '/site?action=del_redirect_multiple',
							param: { site_id: web.id },
							paramId: 'redirectname',
							paramName: 'redirectnames',
							theadName: 'Name',
							confirmVerify: false, // 是否提示验证方式
						},
					},
				],
			});
		},
		templet_proxy: function (sitename, type, obj) {
			if (type) {
				obj = {
					type: 1,
					cache: 0,
					proxyname: '',
					proxydir: '/',
					proxysite: 'http://',
					cachetime: 1,
					todomain: '$host',
					subfilter: [{ sub1: '', sub2: '' }],
				};
			}
			var sub_conter = '';
			for (var i = 0; i < obj.subfilter.length; i++) {
				if (i == 0 || obj.subfilter[i]['sub1'] != '') {
					sub_conter +=
						"<div class='sub-groud'>" +
						"<input name='rep" +
						((i + 1) * 2 - 1) +
						"' class='bt-input-text mr10' placeholder='" +
						lan.site.con_rep_info +
						"' type='text' style='width:200px' value='" +
						obj.subfilter[i]['sub1'] +
						"'>" +
						"<input name='rep" +
						(i + 1) * 2 +
						"' class='bt-input-text ml10' placeholder='" +
						lan.site.to_con +
						"' type='text' style='width:200px' value='" +
						obj.subfilter[i]['sub2'] +
						"'>" +
						"<a href='javascript:;' class='proxy_del_sub' style='color:red;'>Del</a>" +
						'</div>';
				}
				if (i == 2) $('.add-replace-prosy').attr('disabled', 'disabled');
			}
			var helps = [lan.site.proxy_tips1, lan.site.proxy_tips2, lan.site.proxy_tips3, lan.site.proxy_tips4];
			var form_proxy = bt.open({
				type: 1,
				skin: 'demo-class',
				area: '650px',
				title: type ? lan.site.create_proxy : lan.site.modify_proxy + '[' + obj.proxyname + ']',
				closeBtn: 2,
				shift: 5,
				shadeClose: false,
				content:
					"<form id='form_proxy' class='divtable pd15' style='padding-bottom: 60px'>" +
					"<div class='line' style='overflow:hidden'>" +
					"<span class='tname' style='position: relative;top: -5px;'>" +
					lan.site.open_proxy +
					'</span>' +
					"<div class='info-r  ml0 mt5' >" +
					"<input class='btswitch btswitch-ios' id='openVpn' type='checkbox' name='type' " +
					(obj.type == 1 ? 'checked="checked"' : '') +
					"><label class='btswitch-btn phpmyadmin-btn' for='openVpn' style='float:left'></label>" +
					"<div style='display:" +
					(bt.get_cookie('serverType') == 'nginx' ? ' inline-block' : 'none') +
					"'>" +
					"<span class='tname' style='margin-left:15px;position: relative;top: -5px;'>" +
					lan.site.proxy_cache +
					'</span>' +
					"<input class='btswitch btswitch-ios' id='openNginx' type='checkbox' name='cache' " +
					(obj.cache == 1 ? 'checked="checked"' : '') +
					"'><label class='btswitch-btn phpmyadmin-btn' for='openNginx'></label>" +
					'</div>' +
					"<div style='display: inline-block;'>" +
					"<span class='tname' style='position: relative;top: -5px;width:150px;padding-right: 10px;'>" +
					lan.site.proxy_adv +
					'</span>' +
					"<input class='btswitch btswitch-ios' id='openAdvanced' type='checkbox' name='advanced' " +
					(obj.advanced == 1 ? 'checked="checked"' : '') +
					"'><label class='btswitch-btn phpmyadmin-btn' for='openAdvanced'></label>" +
					'</div>' +
					'</div>' +
					'</div>' +
					"<div class='line' style='clear:both;'>" +
					"<span class='tname'>" +
					lan.site.proxy_name +
					'</span>' +
					"<div class='info-r  ml0'><input name='proxyname'" +
					(type ? '' : "readonly='readonly'") +
					" class='bt-input-text mr5 " +
					(type ? '' : ' disabled') +
					"' type='text' style='width:220px' value='" +
					obj.proxyname +
					"'></div>" +
					'</div>' +
					"<div class='line cachetime' style='display:" +
					(obj.cache == 1 ? 'block' : 'none') +
					"'>" +
					"<span class='tname'>" +
					lan.site.cache_time +
					'</span>' +
					"<div class='info-r  ml0'><input name='cachetime'class='bt-input-text mr5' type='text' style='width:220px' value='" +
					obj.cachetime +
					"'>" +
					lan.site.minute +
					'</div>' +
					'</div>' +
					"<div class='line advanced'  style='display:" +
					(obj.advanced == 1 ? 'block' : 'none') +
					"'>" +
					"<span class='tname'>" +
					lan.site.proxy_dir +
					'</span>' +
					"<div class='info-r  ml0'><input id='proxydir' name='proxydir' class='bt-input-text mr5' type='text' style='width:220px' value='" +
					obj.proxydir +
					"'>" +
					'</div>' +
					'</div>' +
					"<div class='line'>" +
					"<span class='tname'>" +
					lan.site.target_url +
					'</span>' +
					"<div class='info-r  ml0'>" +
					"<input name='proxysite' class='bt-input-text mr10' type='text' style='width:220px' value='" +
					obj.proxysite +
					"'>" +
					'</div>' +
					'</div>' +
					"<div class='line'>" +
					"<span class='tname'>" +
					lan.site.proxy_domain +
					'</span>' +
					"<div class='info-r  ml0'>" +
					"<input name='todomain' class='bt-input-text ml10' type='text' style='width:220px' value='" +
					obj.todomain +
					"'>" +
					'</div>' +
					'</div>' +
					"<div class='line replace_conter' style='display:" +
					(bt.get_cookie('serverType') == 'nginx' ? 'block' : 'none') +
					"'>" +
					"<span class='tname'>" +
					lan.site.con_rep +
					'</span>' +
					"<div class='info-r  ml0 '>" +
					sub_conter +
					'</div>' +
					'</div>' +
					"<div class='line' style='display:" +
					(bt.get_cookie('serverType') == 'nginx' ? 'block' : 'none') +
					"'>" +
					"<div class='info-r  ml0'>" +
					"<button class='btn btn-success btn-sm btn-title add-replace-prosy' type='button'><span class='glyphicon cursor glyphicon-plus  mr5' ></span>" +
					lan.site.add_rep_content +
					'</button>' +
					'</div>' +
					'</div>' +
					"<ul class='help-info-text c7'>" +
					bt.render_help(helps) +
					"<div class='bt-form-submit-btn'><button type='button' class='btn btn-sm btn-danger btn-colse-prosy'>" +
					lan.site.turn_off +
					"</button><button type='button' class='btn btn-sm btn-success btn-submit-prosy'>" +
					(type ? ' ' + lan.site.submit : lan.site.save) +
					'</button></div>' +
					'</form>',
			});
			bt.set_cookie('form_proxy', form_proxy);
			$('.add-replace-prosy').click(function () {
				var length = $('.replace_conter .sub-groud').length;
				if (length == 2) $(this).attr('disabled', 'disabled');
				var conter =
					"<div class='sub-groud'>" +
					"<input name='rep" +
					(length * 2 + 1) +
					"' class='bt-input-text mr10' placeholder='" +
					lan.site.con_rep_info +
					"' type='text' style='width:200px' value=''>" +
					"<input name='rep" +
					(length * 2 + 2) +
					"' class='bt-input-text ml10' placeholder='" +
					lan.site.to_con +
					"' type='text' style='width:200px' value=''>" +
					"<a href='javascript:;' class='proxy_del_sub' style='color:red;'>" +
					lan.site.del +
					'</a>' +
					'</div>';
				$('.replace_conter .info-r').append(conter);
			});
			$('[name="proxysite"]').keyup(function () {
				var val = $(this).val(),
					ip_reg = /^(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])$/;
				val = val.replace(/^http[s]?:\/\//, '');
				// val = val.replace(/:([0-9]*)$/, '');
				val = val.replace(/(:|\?|\/|\\)(.*)$/, '');
				if (ip_reg.test(val)) {
					$("[name='todomain']").val('$host');
				} else {
					$("[name='todomain']").val(val);
				}
			});
			$('#openAdvanced').click(function () {
				if ($(this).prop('checked')) {
					$('.advanced').show();
				} else {
					$('.advanced').hide();
				}
			});
			$('#openNginx').click(function () {
				if ($(this).prop('checked')) {
					$('.cachetime').show();
				} else {
					$('.cachetime').hide();
				}
			});
			$('.btn-colse-prosy').click(function () {
				form_proxy.close();
			});
			$('.replace_conter').on('click', '.proxy_del_sub', function () {
				$(this).parent().remove();
				$('.add-replace-prosy').removeAttr('disabled');
			});
			$('.btn-submit-prosy').click(function () {
				var form_proxy_data = {};
				$.each($('#form_proxy').serializeArray(), function () {
					if (form_proxy_data[this.name]) {
						if (!form_proxy_data[this.name].push) {
							form_proxy_data[this.name] = [form_proxy_data[this.name]];
						}
						form_proxy_data[this.name].push(this.value || '');
					} else {
						form_proxy_data[this.name] = this.value || '';
					}
				});
				form_proxy_data['type'] = form_proxy_data['type'] == undefined ? 0 : 1;
				form_proxy_data['cache'] = form_proxy_data['cache'] == undefined ? 0 : 1;
				form_proxy_data['advanced'] = form_proxy_data['advanced'] == undefined ? 0 : 1;
				form_proxy_data['sitename'] = sitename;
				form_proxy_data['subfilter'] = JSON.stringify([
					{ sub1: form_proxy_data['rep1'] || '', sub2: form_proxy_data['rep2'] || '' },
					{ sub1: form_proxy_data['rep3'] || '', sub2: form_proxy_data['rep4'] || '' },
					{ sub1: form_proxy_data['rep5'] || '', sub2: form_proxy_data['rep6'] || '' },
				]);
				for (var i in form_proxy_data) {
					if (i.indexOf('rep') != -1) {
						delete form_proxy_data[i];
					}
				}
				if (type) {
					bt.site.create_proxy(form_proxy_data, function (rdata) {
						if (rdata.status) {
							form_proxy.close();
							site.reload(12);
						}
						bt.msg(rdata);
					});
				} else {
					bt.site.modify_proxy(form_proxy_data, function (rdata) {
						if (rdata.status) {
							form_proxy.close();
							site.reload(12);
						}
						bt.msg(rdata);
					});
				}
			});
		},
		set_proxy: function (web) {
			var limit_len = bt.get_cookie('serverType') == 'nginx' ? 'proxy_list_limit_4' : 'proxy_list_limit_3';
			$('#webedit-con').html('<div id="proxy_list" class="' + limit_len + '"></div>');
			String.prototype.myReplace = function (f, e) {
				//吧f替换成e
				var reg = new RegExp(f, 'g'); //创建正则RegExp对象
				return this.replace(reg, e);
			};
			bt_tools.table({
				el: '#proxy_list',
				url: '/site?action=GetProxyList',
				param: { sitename: web.name },
				dataFilter: function (res) {
					return { data: res };
				},
				column: [
					{ type: 'checkbox', width: 20 },
					{
						fid: 'proxyname',
						title: lan.site.name,
						template: function (row, index) {
							return '<span class="limit-text-length" style="max-width: 50px" title="' + row.proxyname + '">' + row.proxyname + '</span>';
						},
					},
					{
						fid: 'proxydir',
						title: lan.site.proxy_dir,
						template: function (row, index) {
							return '<span class="limit-text-length" style="max-width: 40px" title="' + row.proxydir + '">' + row.proxydir + '</span>';
						},
					},
					{ fid: 'proxysite', title: lan.site.target_url, type: 'link', href: true },
					bt.get_cookie('serverType') == 'nginx'
						? {
								fid: 'cache',
								title: lan.site.cache,
								config: {
									icon: false,
									list: [
										[1, lan.site.already_open, 'bt_success'],
										[0, lan.site.already_close, 'bt_danger'],
									],
								},
								type: 'status',
								event: function (row, index, ev, key, that) {
									row['cache'] = !row['cache'] ? 1 : 0;
									row['subfilter'] = JSON.stringify(row['subfilter']);
									bt.site.modify_proxy(row, function (rdata) {
										row['subfilter'] = JSON.parse(row['subfilter']);
										if (rdata.status) that.$modify_row_data({ cache: row['cache'] });
										bt.msg(rdata);
									});
								},
						  }
						: {},
					{
						fid: 'type',
						title: lan.site.status,
						config: {
							icon: true,
							list: [
								[1, lan.site.running_text, 'bt_success', 'glyphicon-play'],
								[0, lan.site.already_stop, 'bt_danger', 'glyphicon-pause'],
							],
						},
						type: 'status',
						event: function (row, index, ev, key, that) {
							row['type'] = !row['type'] ? 1 : 0;
							row['subfilter'] = JSON.stringify(row['subfilter']);
							bt.site.modify_proxy(row, function (rdata) {
								row['subfilter'] = JSON.parse(row['subfilter']);
								if (rdata.status) that.$modify_row_data({ type: row['type'] });
								bt.msg(rdata);
							});
						},
					},
					{
						title: lan.site.operate,
						width: 115,
						type: 'group',
						align: 'right',
						group: [
							{
								title: 'Conf',
								event: function (row, index, ev, key, that) {
									bt.site.get_proxy_config(
										{
											sitename: web.name,
											proxyname: row.proxyname,
											webserver: bt.get_cookie('serverType'),
										},
										function (rdata) {
											if (typeof rdata == 'object' && rdata.constructor == Array) {
												if (!rdata[0].status) bt.msg(rdata);
											} else {
												if (!rdata.status) bt.msg(rdata);
											}
											var datas = [
												{
													items: [
														{
															name: 'proxy_configs',
															type: 'textarea',
															value: rdata[0].data,
															widht: '340px',
															height: '200px',
														},
													],
												},
												{
													name: 'btn_config_submit',
													text: 'Save',
													type: 'button',
													callback: function (ddata) {
														bt.site.save_proxy_config(
															{
																path: rdata[1],
																data: editor.getValue(),
																encoding: rdata[0].encoding,
															},
															function (ret) {
																if (ret.status) {
																	site.reload(12);
																	proxy_config.close();
																}
																bt.msg(ret);
															}
														);
													},
												},
											];
											proxy_config = bt.open({
												type: 1,
												area: ['550px', '550px'],
												title: 'Edit profile [' + row.proxyname + ']',
												closeBtn: 2,
												shift: 0,
												content: "<div class='bt-form'><div id='proxy_config_con' class='pd15'></div></div>",
											});
											var robj = $('#proxy_config_con');
											for (var i = 0; i < datas.length; i++) {
												var _form_data = bt.render_form_line(datas[i]);
												robj.append(_form_data.html);
												bt.render_clicks(_form_data.clicks);
											}
											robj.append(bt.render_help(['This is the configuration file of the load balancing. Not modify if you do not understand the configuration rules.']));
											$('textarea.proxy_configs').attr('id', 'configBody');
											var editor = CodeMirror.fromTextArea(document.getElementById('configBody'), {
												extraKeys: { 'Ctrl-Space': 'autocomplete' },
												lineNumbers: true,
												matchBrackets: true,
											});
											$('.CodeMirror-scroll').css({ height: '350px', margin: 0, padding: 0 });
											setTimeout(function () {
												editor.refresh();
											}, 250);
										}
									);
								},
							},
							{
								title: 'Edit',
								event: function (row, index, ev, key, that) {
									site.edit.templet_proxy(web.name, false, row);
								},
							},
							{
								title: 'Del',
								event: function (row, index, ev, key, that) {
									bt.site.remove_proxy(web.name, row.proxyname, function (rdata) {
										if (rdata.status) that.$delete_table_row(index);
									});
								},
							},
						],
					},
				],
				tootls: [
					{
						//按钮组
						type: 'group',
						positon: ['left', 'top'],
						list: [
							{
								title: 'Add reverse proxy',
								active: true,
								event: function (ev) {
									site.edit.templet_proxy(web.name, true);
								},
							},
						],
					},
					{
						//批量操作
						type: 'batch',
						positon: ['left', 'bottom'],
						config: {
							title: ' delete',
							url: '/site?action=del_proxy_multiple',
							param: { site_id: web.id },
							paramId: 'proxyname',
							paramName: 'proxynames',
							theadName: 'Name',
							confirmVerify: false, // 是否提示验证方式
						},
					},
				],
			});
		},
		set_security: function (web) {
			bt.site.get_site_security(web.id, web.name, function (rdata) {
				var robj = $('#webedit-con');
				var datas = [
					{
						title: lan.site.url_suffix,
						name: 'sec_fix',
						value: rdata.fix,
						disabled: rdata.status,
						width: '300px',
					},
					{
						title: lan.site.access_domain1,
						items: [
							{
								text: lan.site.start_anti_leech,
								name: 'sec_domains',
								width: '300px',
								height: '210px',
								disabled: rdata.status,
								value: rdata.domains.replace(/,/g, '\n'),
								type: 'textarea',
							},
						],
					},
					{
						title: 'Response',
						name: 'return_rule',
						value: rdata.return_rule,
						disabled: rdata.status,
						width: '300px',
					},
					{
						title: ' ',
						class: 'label-input-group',
						items: [
							{
								text: lan.site.start_anti_leech,
								name: 'status',
								value: rdata.status,
								type: 'checkbox',
								callback: function (sdata) {
									bt.site.set_site_security(web.id, web.name, sdata.sec_fix, sdata.sec_domains.split('\n').join(','), sdata.status, sdata.return_rule, function (ret) {
										if (ret.status) site.reload(13);
										bt.msg(ret);
									});
								},
							},
							{
								text: 'Allow empty HTTP_REFERER requests',
								name: 'none',
								value: rdata.none,
								type: 'checkbox',
								callback: function (sdata) {
									bt.site.set_site_security(web.id, web.name, sdata.sec_fix, sdata.sec_domains.split('\n').join(','), '1', sdata.return_rule, function (ret) {
										if (ret.status) site.reload(13);
										bt.msg(ret);
									});
								},
							},
						],
					},
				];

				for (var i = 0; i < datas.length; i++) {
					var _form_data = bt.render_form_line(datas[i]);
					robj.append(_form_data.html);
					bt.render_clicks(_form_data.clicks);
				}
				robj.find('#none').css('margin-top', '10px');
				$('#none').before('</br>');
				var helps = [lan.site.access_empty_ref_default, lan.site.multi_url, lan.site.trigger_return_404];
				robj.append(bt.render_help(helps));
			});
		},
		set_tomact: function (web) {
			bt.site.get_site_phpversion(web.name, function (rdata) {
				var robj = $('#webedit-con');
				if (!rdata.tomcatversion) {
					robj.html('<font>' + lan.site.tomcat_err_msg1 + '</font>');
					layer.msg(lan.site.tomcat_err_msg, { icon: 2 });
					return;
				}
				var data = {
					class: 'label-input-group',
					items: [
						{
							text: lan.site.enable_tomcat,
							name: 'tomcat',
							value: rdata.tomcat == -1 ? false : true,
							type: 'checkbox',
							callback: function (sdata) {
								bt.site.set_tomcat(web.name, function (ret) {
									if (ret.status) site.reload(9);
									bt.msg(ret);
								});
							},
						},
					],
				};
				var _form_data = bt.render_form_line(data);
				robj.append(_form_data.html);
				bt.render_clicks(_form_data.clicks);
				var helps = [lan.site.tomcat_help1 + ' ' + rdata.tomcatversion + ',' + lan.site.tomcat_help2, lan.site.tomcat_help3, lan.site.tomcat_help4, lan.site.tomcat_help5];
				robj.append(bt.render_help(helps));
			});
		},
		get_site_logs: function (web) {
			$('#webedit-con').append('<div id="tabLogs" class="tab-nav"></div><div class="tab-con" style="padding:10px 0 0;"></div>');
			var serverType = bt.get_cookie('serverType'),
				shell = 'tail -n 100 -f /www/wwwlogs/' + web.name;
			var _tab = [
				{
					title: 'Access log',
					on: true,
					callback: function (robj) {
						bt.site.get_site_logs(web.name, function (rdata) {
							var _logs_info = $('<div></div>').text(rdata.msg);
							var logs = { class: 'bt-logs', items: [{ name: 'site_logs', height: '560px', value: _logs_info.html(), width: '100%', type: 'textarea' }] },
								_form_data = bt.render_form_line(logs);
							robj.append(_form_data.html);
							bt.render_clicks(_form_data.clicks);
							$('textarea[name="site_logs"]').attr('readonly', true);
							$('textarea[name="site_logs"]').scrollTop(100000000000);
						});
					},
				},
				{
					title: 'Error log',
					callback: function (robj) {
						bt.site.get_site_error_logs(web.name, function (rdata) {
							var _logs_info = $('<div></div>').text(rdata.msg);
							var logs = { class: 'bt-logs', items: [{ name: 'site_logs', height: '560px', value: _logs_info.html(), width: '100%', type: 'textarea' }] },
								_form_data = bt.render_form_line(logs);
							robj.append(_form_data.html);
							bt.render_clicks(_form_data.clicks);
							$('textarea[name="site_logs"]').attr('readonly', true);
							$('textarea[name="site_logs"]').scrollTop(100000000000);
						});
					},
				},
				{
					title: 'Log Security Analysis',
					callback: function (robj) {
						var _serverType = bt.get_cookie('serverType'),
							pathFile = '',
							progress = '', //扫描进度
							loadT = bt.load('Getting log analytics data, please wait...');

						switch (_serverType) {
							case 'nginx':
								pathFile = web.name + '.log';
								break;
							case 'apache':
								pathFile = web.name + '-access_log';
								break;
							default:
								pathFile = web.name + '_ols.access_log';
								break;
						}
						$.post('/ajax?action=get_result&path=/www/wwwlogs/' + pathFile, function (rdata) {
							loadT.close();
							//1.扫描按钮
							var analyes_log_btn = '<button type="button" title="log scan" class="btn btn-success analyes_log btn-sm mr5"><span>log scan</span></button>';

							//2.功能介绍
							var analyse_help =
								'<ul class="help-info-text c7">\
                      <li>Log analysis: Scan the logs(/www/wwwroot/.log) for requests with attack (types include:<em style="color:red">xss,sql,san,php</em>)</li>\
                      <li>Analyzed log data contains intercepted requests</li>\
                      <li>By default, the last scan data is displayed (if not, please click log scan)</li>\
                      <li>If the log file is too large, scanning may take a long time, please be patient</li>\
                      <li><a class="btlink" href="https://www.aapanel.com/forum/d/3351-nginx-waf-instructions" target="_blank">aaPanel WAF</a> can effectively block such attacks</li>\
                      </ul>';

							robj.append(analyes_log_btn + '<div class="analyse_log_table"></div>' + analyse_help);
							render_analyse_list(rdata);

							//事件
							$(robj)
								.find('.analyes_log')
								.click(function () {
									bt.confirm(
										{
											title: 'Scan website logs',
											msg:
												'It is recommended to perform security analysis when the server load is low. This time, the [' +
												web.name +
												'.log] file will be scanned. It may take a long time. Do you want to continue?',
										},
										function (index) {
											layer.close(index);
											progress = layer.open({
												type: 1,
												closeBtn: 2,
												title: false,
												shade: 0,
												area: '400px',
												content:
													'<div class="pro_style" style="padding: 20px;"><div class="progress-head" style="padding-bottom: 10px;">Scanning, scanning progress...</div>\
                              <div class="progress">\
                                <div class="progress-bar progress-bar-success progress-bar-striped" role="progressbar" aria-valuenow="40" aria-valuemin="0" aria-valuemax="100" style="width: 0%">0%</div>\
                              </div>\
                            </div>',
												success: function () {
													// 开启扫描并且持续获取进度
													$.post('/ajax?action=log_analysis&path=/www/wwwlogs/' + pathFile, function (rdata) {
														if (rdata.status) {
															detect_progress();
														} else {
															layer.close(progress);
															layer.msg(rdata.msg, { icon: 2, time: 0, shade: 0.3, shadeClose: true });
														}
													});
												},
											});
										}
									);
								});
						});
						// 渲染分析日志列表
						function render_analyse_list(rdata) {
							var analyse_list =
								'<div class="divtable" style="margin-top: 10px;"><table class="table table-hover">\
                      <thead><tr><th width="90">Date</th><th>Time</th><th>XSS</th><th>SQL</th><th>Sacn</th><th>PHP</th><th>IP(top100)</th><th>URL(top100)</th></tr></thead>\
                      <tbody class="analyse_body">';
							if (rdata.is_status) {
								//检测是否有扫描数据
								analyse_list +=
									'<tr>\
                          <td>' +
									rdata.start_time +
									'</td>\
                          <td>' +
									rdata.time.substring(0, 4) +
									' Sec</td>\
                          <td class="onChangeLogDatail" ' +
									(rdata.xss > 0 ? 'style="color:red"' : '') +
									' name="xss">' +
									rdata.xss +
									'</td>\
                          <td class="onChangeLogDatail" ' +
									(rdata.sql > 0 ? 'style="color:red"' : '') +
									' name="sql">' +
									rdata.sql +
									'</td>\
                          <td class="onChangeLogDatail" ' +
									(rdata.san > 0 ? 'style="color:red"' : '') +
									' name="san">' +
									rdata.san +
									'</td>\
                          <td class="onChangeLogDatail" ' +
									(rdata.php > 0 ? 'style="color:red"' : '') +
									' name="php">' +
									rdata.php +
									'</td>\
                          <td class="onChangeLogDatail" style="color:#20a53a" name="ip">' +
									rdata.ip +
									'</td>\
                          <td class="onChangeLogDatail" style="color:#20a53a" name="url">' +
									rdata.url +
									'</td>\
                        </tr>';
							} else {
								analyse_list += '<tr><td colspan="9" style="text-align: center;">no scan data</td></tr>';
							}
							analyse_list += '</tbody></table></div>';
							$('.analyse_log_table').html(analyse_list);
							$('.onChangeLogDatail').css('cursor', 'pointer').attr('title', 'Details');
							//查看详情
							$('.onChangeLogDatail').on('click', function () {
								get_analysis_data_datail($(this).attr('name'));
							});
						}
						// 扫描进度
						function detect_progress() {
							$.post('/ajax?action=speed_log&path=/www/wwwlogs/' + pathFile, function (res) {
								var pro = res.msg;
								if (pro !== 100) {
									if (pro > 100) pro = 100;
									if (pro !== NaN) {
										$('.pro_style .progress-bar')
											.css('width', pro + '%')
											.html(pro + '%');
									}
									setTimeout(function () {
										detect_progress();
									}, 1000);
								} else {
									layer.msg('Scan complete', { icon: 1, timeout: 4000 });
									layer.close(progress);
									get_analysis_data();
								}
							});
						}
						// 获取扫描结果
						function get_analysis_data() {
							var loadTGA = bt.load('Getting log analytics data, please wait...');
							$.post('/ajax?action=get_result&path=/www/wwwlogs/' + pathFile, function (rdata) {
								loadTGA.close();
								render_analyse_list(rdata, true);
							});
						}
						// 获取扫描结果详情日志
						function get_analysis_data_datail(name) {
							layer.open({
								type: 1,
								closeBtn: 2,
								shadeClose: false,
								title: '[ ' + name + ' ] log details',
								area: '650px',
								content: '<pre id="analysis_pre" style="background-color: #333;color: #fff;height: 545px;margin: 0;white-space: pre-wrap;border-radius: 0;"></pre>',
								success() {
									var loadTGD = bt.load('Getting log details data, please wait...');
									$.post('/ajax?action=get_detailed&path=/www/wwwlogs/' + pathFile + '&type=' + name + '', function (logs) {
										loadTGD.close();
										$('#analysis_pre').text((name == 'ip' || name == 'url' ? ' [Access Times] [' + name + '] \n' : '') + logs);
									});
								},
							});
						}
					},
				},
			];
			bt.render_tab('tabLogs', _tab);
			$('#tabLogs span:eq(0)').click();
		},
	},
	create_let: function (ddata, callback) {
		bt.site.create_let(ddata, function (ret) {
			if (ret.status) {
				if (callback) {
					callback(ret);
				} else {
					site.ssl.reload(1);
					bt.msg(ret);
					return;
				}
			} else {
				if (ret.msg) {
					if (typeof ret.msg == 'string') {
						ret.msg = [ret.msg, ''];
					}
				}
				if (!ret.out) {
					if (callback) {
						callback(ret);
						return;
					}
					bt.msg(ret);
					return;
				}
				var data = '<p>' + ret.msg + '</p><hr />';
				if (ret.err[0].length > 10) data += '<p style="color:red;">' + ret.err[0].replace(/\n/g, '<br>') + '</p>';
				if (ret.err[1].length > 10) data += '<p style="color:red;">' + ret.err[1].replace(/\n/g, '<br>') + '</p>';

				layer.msg(data, { icon: 2, area: '500px', time: 0, shade: 0.3, shadeClose: true });
			}
		});
	},
	reload: function (index) {
		if (index == undefined) index = 0;

		var _sel = $('.site-menu p.bgw');
		if (_sel.length == 0) _sel = $('.site-menu p:eq(0)');
		_sel.trigger('click');
	},
	plugin_firewall: function () {
		var typename = bt.get_cookie('serverType');
		var name = 'btwaf_httpd';
		if (typename == 'nginx') name = 'btwaf';

		bt.plugin.get_plugin_byhtml(name, function (rhtml) {
			if (rhtml.status === false) return;

			var list = rhtml.split('<script type="javascript/text">');
			if (list.length > 1) {
				rcode = rhtml.split('<script type="javascript/text">')[1].replace('</script>', '');
			} else {
				list = rhtml.split('<script type="text/javascript">');
				rcode = rhtml.split('<script type="text/javascript">')[1].replace('</script>', '');
			}
			rcss = rhtml.split('<style>')[1].split('</style>')[0];
			rcode = rcode.replace('    wafview()', '');
			$('body').append('<div style="display:none"><style>' + rcss + '</style><script type="javascript/text">' + rcode + '</script></div>');

			setTimeout(function () {
				if (!!(window.attachEvent && !window.opera)) {
					execScript(rcode);
				} else {
					window.eval(rcode);
				}
			}, 200);
		});
	},
	select_site_txt: function (box, value) {
		var that = this;
		layer.open({
			type: 1,
			closeBtn: 2,
			title: lan.site.set_ssl.cust_domain,
			area: '600px',
			btn: [lan.public.ok, lan.public.cancel],
			content:
				'<div class="pd20"><div class="line "><span class="tname">Domain name</span><div class="info-r "><input  name="site_name" placeholder="' +
				lan.site.set_ssl.cust_place +
				'" class="bt-input-text mr5 ssl_site_name_rc" type="text" value="' +
				value +
				'" style="width:400px" value=""></div></div>\
							<ul class="help-info-text c7">\
											<li> ' +
				lan.site.set_ssl.cust_tip1 +
				'</li>\
											<li>' +
				lan.site.set_ssl.cust_tip2 +
				'</li>\
											<li>' +
				lan.site.set_ssl.cust_tip3 +
				'</li>\
											<li>    1、' +
				lan.site.set_ssl.cust_tip4 +
				'</li>\
											<li>    2、' +
				lan.site.set_ssl.cust_tip5 +
				'</li>\
											<li>    3、' +
				lan.site.set_ssl.cust_tip6 +
				'</li>\
									</ul >\
							</div>',
			success: function () {
				$('[name="site_name"]').focus();
			},
			yes: function (layers, index) {
				var domain = $('.ssl_site_name_rc').val(),
					code = $('.perfect_ssl_info').data('code');
				if (!bt.check_domain(domain)) {
					return layer.msg(lan.site.set_ssl.sing_domain_err, { icon: 2 });
				} else if (code.indexOf('wildcard') === -1) {
					if (domain.indexOf('*') > -1) {
						return layer.msg(lan.site.set_ssl.sing_domain_more, { icon: 2 });
					}
				}
				layer.close(layers);
				$('#' + box).val($('.ssl_site_name_rc').val());
				// that.check_domain_error(domain);
				that.check_domain_dns();
			},
		});
	},
	/**
	 * @descripttion: 选择站点
	 * @author: Lifu
	 * @Date: 2020-08-14
	 * @param {String} box 输出时所用ID
	 * @return: 无返回值
	 */
	select_site_list: function (box, code) {
		var that = this,
			_optArray = [],
			all_site_list = [];
		bt.send('getData', 'data/getData', { tojs: 'site.get_list', table: 'domain', limit: 10000, search: '', p: 1, order: 'id desc', type: -1 }, function (res) {
			var _tbody = '';
			if (res.data.length > 0) {
				$.each(res.data, function (index, item) {
					_body =
						'<tr>' +
						'<td>' +
						'<div class="box-group" style="height:16px">' +
						'<div class="bt_checkbox_groups"></div>' +
						'</div>' +
						'</td>' +
						'<td><span class="overflow_style" style="width:210px">' +
						item['name'] +
						'</span></td>' +
						'</tr>';
					if (code.indexOf('wildcard') > -1) {
						if (item['name'].indexOf('*.') > -1) {
							all_site_list.push(item['name']);
							_tbody += _body;
						}
					} else {
						all_site_list.push(item['name']);
						_tbody += _body;
					}
				});
				if (all_site_list.length == 0) {
					_tbody = '<tr><td colspan="2">' + lan.bt.no_data + '</td></tr>';
				}
			} else {
				_tbody = '<tr><td colspan="2">' + lan.bt.no_data + '</td></tr>';
			}

			layer.open({
				type: 1,
				closeBtn: 2,
				title: lan.site.set_ssl.select_domain,
				area: ['600px', '650px'],
				btn: [lan.public.ok, lan.public.cancel],
				content:
					'\
					<div class="pd20 dynamic_head_box">\
						<div class="line">\
							<input type="text" name="serach_site" class="bt-input-text" style="width: 550px;" placeholder="' +
					lan.site.set_ssl.sup_fuzzy +
					'">\
						</div>\
						<div class="dynamic_list_table">\
							<div class="divtable" style="height:281px">\
								<table class="table table-hover">\
									<thead>\
										<th width="30">\
											<div class="box-group" style="height:16px">\
												<div class="bt_checkbox_groups" data-key="0"></div>\
											</div>\
										</th>\
										<th>' +
					lan.site.set_ssl.domain_name +
					'</th>\
									</thead>\
									<tbody class="dynamic_list">' +
					_tbody +
					'</tbody>\
								</table>\
							</div>\
						</div>\
						<ul class="help-info-text c7">\
							<li> ' +
					lan.site.set_ssl.cust_tip1 +
					'</li>\
							<li>' +
					lan.site.set_ssl.cust_tip2 +
					'</li>\
							<li>' +
					lan.site.set_ssl.cust_tip3 +
					'</li>\
							<li>    1、' +
					lan.site.set_ssl.cust_tip4 +
					'</li>\
							<li>    2、' +
					lan.site.set_ssl.cust_tip5 +
					'</li>\
							<li>    3、' +
					lan.site.set_ssl.cust_tip6 +
					'</li>\
						</ul>\
					</div> ',
				success: function () {
					// 固定表格头部
					if (jQuery.prototype.fixedThead) {
						$('.dynamic_list_table .divtable').fixedThead({ resize: false });
					} else {
						$('.dynamic_list_table .divtable').css({ overflow: 'auto' });
					}
					//检索输入
					$('input[name=serach_site]').on('input', function () {
						var _serach = $(this).val();
						if (_serach.trim() != '') {
							$('.dynamic_list tr').each(function () {
								var _td = $(this).find('td').eq(1).html();
								if (_td.indexOf(_serach) == -1) {
									$(this).hide();
								} else {
									$(this).show();
								}
							});
						} else {
							$('.dynamic_list tr').show();
						}
					});

					// 单选设置
					$('.dynamic_list').on('click', '.bt_checkbox_groups', function (e) {
						var _tr = $(this).parents('tr');
						if ($(this).hasClass('active')) {
							$(this).removeClass('active');
						} else {
							$('.dynamic_list .bt_checkbox_groups').removeClass('active');
							$(this).addClass('active');
							_optArray = [_tr.find('td').eq(1).text()];
						}
						e.preventDefault();
						e.stopPropagation();
					});
					// tr点击时
					$('.dynamic_list').on('click', 'tr', function (e) {
						$(this).find('.bt_checkbox_groups').click();
						e.preventDefault();
						e.stopPropagation();
					});
				},
				yes: function (layers, index) {
					var _olist = [];
					if (_optArray.length > 0) {
						$.each(_optArray, function (index, item) {
							if ($.inArray(item, _olist) == -1) {
								_olist.push(item);
							}
						});
					}
					layer.close(layers);
					// 多域名时，将olist过滤并追加到site.domain_dns_list
					if (site.domain_dns_type == 'multi') {
						var domainList = site.domain_dns_list;
						var newDomainList = [];
						$.each(_olist, function (index, item) {
							if ($.inArray(item, domainList) == -1) {
								newDomainList.push(item);
							}
						});
						domainList = domainList.concat(newDomainList);
					} else {
						domainList = _olist;
					}
					$('#' + box).val(domainList.join('\n'));
					site.domain_dns_list = domainList;
					$('textarea[name=lb_site]').focus();

					// that.check_domain_error(_olist[0]);
					that.check_domain_dns();
				},
			});
		});
	},
	web_edit: function (obj) {
		var _this = this;
		var item = obj;
		bt.open({
			type: 1,
			area: ['860px', '740px'],
			title: lan.site.website_change + ' [' + item.name + ']  --  ' + lan.site.addtime + ' [' + item.addtime + ']',
			closeBtn: 2,
			shift: 0,
			content: "<div class='bt-form'><div class='bt-w-menu site-menu pull-left' style='height: 100%;'></div><div id='webedit-con' class='bt-w-con webedit-con pd15'></div></div>",
		});
		setTimeout(function () {
			var webcache =
				bt.get_cookie('serverType') == 'openlitespeed'
					? {
							title: 'LS-Cache',
							callback: site.edit.ols_cache,
					  }
					: '';
			var menus = [
				{ title: lan.site.domain_man, callback: site.edit.set_domains },
				{ title: lan.site.site_menu_1, callback: site.edit.set_dirbind },
				{ title: lan.site.site_menu_2, callback: site.edit.set_dirpath },
				{ title: 'Limit access', callback: site.edit.set_dirguard },
				{ title: lan.site.site_menu_3, callback: site.edit.limit_network },
				{ title: lan.site.site_menu_4, callback: site.edit.get_rewrite_list },
				{ title: lan.site.site_menu_5, callback: site.edit.set_default_index },
				{ title: lan.site.site_menu_6, callback: site.edit.set_config },
				{ title: lan.site.site_menu_7, callback: site.set_ssl },
				{ title: lan.site.php_ver, callback: site.edit.set_php_version },
				{ title: 'Composer', callback: site.edit.set_composer },
				// { title: lan.site.site_menu_9, callback: site.edit.set_tomact },
				// { title: lan.site.redirect, callback: site.edit.set_301_old },
				{ title: lan.site.redirect_test, callback: site.edit.set_301 },
				{ title: lan.site.site_menu_11, callback: site.edit.set_proxy },
				{ title: lan.site.site_menu_12, callback: site.edit.set_security },
				{ title: lan.site.response_log, callback: site.edit.get_site_logs },
			];
			if (webcache !== '') menus.splice(3, 0, webcache);
			if (item.project_type == 'WP') menus.splice(10, 0, { title: 'Wordpress Setting', callback: site.edit.set_wp_config });
			for (var i = 0; i < menus.length; i++) {
				var men = menus[i];
				var _p = $('<p>' + men.title + '</p>');
				_p.data('callback', men.callback);
				$('.site-menu').append(_p);
			}
			$('.site-menu p').click(function () {
				$('#webedit-con').html('');
				$(this).addClass('bgw').siblings().removeClass('bgw');
				var callback = $(this).data('callback');
				if (callback) callback(item);
			});
			site.reload(0);
		}, 100);
	},
	domain_dns_list: [], // dns域名列表
	domain_dns_type: '', // dns域名类型[one/multi]
	dns_data_treating: [], // 原始dns接口数据
	dns_configured_table: [], // 已配置的dns域名列表
	dns_interface_list: [], // dns接口列表
	dnsForm: null,
	//检测域名api配置是否正确
	check_domain_dns: function () {
		if (site.domain_dns_type == 'one') {
			var domain = $('#apply_site_name').val();
			site.domain_dns_list = [domain];
			if (domain == '') return layer.msg(lan.site.set_ssl.domain_name_pl, { icon: 0 });
		} else if (site.domain_dns_type == 'multi') {
			if (site.domain_dns_list.length == 0) return layer.msg(lan.site.set_ssl.domain_name_pla, { icon: 0 });
		}
		site.refresh_dns_interface();
	},
	// 管理dns接口
	set_dns_api_open: function () {
		bt_tools.open({
			title: lan.site.set_ssl.man_dns,
			area: '600px',
			btn: false,
			content: '<div class="dnsManager pd20"></div>',
			success: function (layers) {
				bt_tools.table({
					el: '.dnsManager',
					url: '/site?action=GetDnsApi',
					height: '400',
					dataFilter: function (res) {
						var data = [];
						for (var i = 1; i < res.length; i++) {
							var resI = res[i];
							for (var j = 0; j < resI.data.length; j++) {
								var info = {};
								info = {
									ps: resI.data[j].ps,
									id: resI.data[j].id,
									domain: resI.data[j].domain,
									conf: resI.data[j].conf,
									typeTitle: resI.title,
									dns_type: resI.name,
									name: resI.data[j].conf[0].value,
									value: resI.data[j].conf[1].value,
								};
								// 获取dns接口配置信息
								for (var k = 0; k < resI.data[j].conf.length; k++) {
									info[resI.data[j].conf[k].name] = resI.data[j].conf[k].value;
								}
								data.push(info);
							}
						}
						site.dns_configured_table = site.data_treating(res);
						return { data: data };
					},
					column: [
						{
							fid: 'typeTitle',
							title: lan.public_backup.type,
						},
						{
							fid: 'ps',
							title: lan.soft.ps,
						},
						{
							title: bt.public.action,
							align: 'right',
							type: 'group',
							group: [
								{
									title: bt.public.edit,
									event: function (row, index, ev, key, _that) {
										site.editDns(row, _that);
									},
								},
								{
									title: bt.public.del,
									event: function (row, index, ev, key, _that) {
										bt.simple_confirm({ title: 'delete【' + row.ps + '】', msg: lan.site.set_ssl.del_api_confirm + '？' }, function () {
											bt_tools.send(
												{ url: '/site?action=remove_dns_api', data: { dns_type: row.dns_type, api_id: row.id } },
												function (res) {
													bt_tools.msg(res);
													if (res.status) _that.$refresh_table_list(true);
												},
												'Delete authentication interface'
											);
										});
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
									title: lan.site.set_ssl.add_dns,
									active: true,
									event: function (row, _that) {
										site.editDns(undefined, _that);
									},
								},
							],
						},
					],
				});
			},
		});
	},

	// 添加dns接口
	add_dns_interface: function () {
		var _this = this;
		if ($('.dns_interface_line').length > 0) return;
		$('.check_model_line.line').after('<div class="dns_interface_line line"><div class="dnsForm"></div></div>'); // 插入dns
		$('.isdnsbtn').show(); // 显示dns刷新按钮
		var formConfig = [
			{
				label: lan.site.set_ssl.select_dns,
				group: [
					{
						type: 'select',
						name: 'dns_select',
						width: '250px',
						placeholder: lan.site.set_ssl.select_parse,
						list: [
							// {title:lan.site.set_ssl.auto_parse,value:'dns#@api'},
							{ title: lan.site.set_ssl.manual_parse, value: 'dns' },
						],
						change: function (formData, el, that) {
							that.config.form[0].group[0].value = formData.dns_select;
							if (formData.dns_select == 'dns#@api') {
								that.config.form[0].group[0].suffix = '';
								that.config.form[0].group[1].display = true;
							} else {
								that.config.form[0].group[0].suffix = '<br><span class="c7">' + lan.site.set_ssl.parse_tip + '</span>';
								that.config.form[0].group[1].display = false;
							}
							that.$replace_render_content(0);
						},
					},
					{
						display: false,
						type: 'button',
						class: 'btn-sub-success',
						style: { 'margin-left': '10px', 'vertical-align': 'middle' },
						title: lan.site.set_ssl.dns_api_config,
					},
				],
			},
		];
		if ($('#ssl_tabs span.on').text().indexOf('Let') > -1) {
			// formConfig插入数据
			formConfig.push(
				{
					label: '',
					group: [
						{
							name: 'app_root',
							type: 'checkbox',
							title: lan.site.set_ssl.auto_more_domain,
						},
					],
				},
				{
					label: '',
					group: [
						{
							type: 'help',
							style: { margin: '0' },
							list: [lan.site.set_ssl.auto_more_tip],
						},
					],
				}
			);
		}
		// 渲染dns
		_this.dnsForm = bt_tools.form({
			el: '.dnsForm',
			form: formConfig,
		});
		//管理dns点击事件
		$('.dnsForm')
			.unbind('click')
			.on('click', '.btn-sub-success.btn-success', function () {
				site.set_dns_api_open();
			});
	},
	// 添加/编辑dns接口
	editDns: function (row, _that, isGlobal) {
		var isEdit = row && row.hasOwnProperty('name') ? true : false;
		bt_tools.open({
			title: isEdit ? 'Edit【' + row.ps + '】' : lan.site.set_ssl.add_dns_ver,
			area: '530px',
			skin: 'dns_layer_form',
			content: {
				class: 'pd20',
				data: row,
				form: this.switch_dns_add_key(isEdit ? row.dns_type : site.dns_interface_list[0].value, isGlobal),
			},
			success: function (layero) {
				$('.dns-help li').eq(3).show().siblings().hide();
				$(layero).find('.layui-layer-content').css('overflow', 'inherit');
				if (isGlobal) {
					$('textarea[name=domains]').val(isEdit ? row.domain.join('\n') : '');
				}
			},
			yes: function (formData, indexs) {
				// 是否验证成功
				var isverify = true,
					param = { dns_type: formData.dns_type, ps: formData.ps },
					paramArr = [];
				// 限制ps的长度
				if (formData.ps.length > 35) return layer.msg(lan.site.set_ssl.ps_pl, { icon: 0 });
				// dns_layer_form下input如果为空，提示对应的placeholder，然后return false
				$('.dns_layer_form input').each(function (index, item) {
					var _val = $(item).val();
					if (_val == '' || _val.replace(/\s+/g, '') == '') {
						layer.msg($(item).attr('placeholder'), { icon: 0 });
						isverify = false;
						return false;
					}
				});
				if (!isverify) return false;
				// 排除formData中的dns_type和ps,循环添加到paramArr中
				for (var key in formData) {
					if (key !== 'dns_type' && key !== 'ps') {
						paramArr.push({ name: key, value: formData[key] });
					}
				}
				param['pdata'] = JSON.stringify(paramArr);

				if (isEdit) param['api_id'] = row.id;
				if (typeof row != 'undefined' && row.hasOwnProperty('domains')) {
					param['domains'] = JSON.stringify([row.domains]); // 没有dns接口，默认已当前域名添加
				} else if (isGlobal) {
					// 高级设置类型
					param['domains'] = JSON.stringify(formData.domains.split('\r\n'));
				} else {
					param['domains'] = JSON.stringify([]); //不设定固定域名，单纯链接dns接口
				}
				bt_tools.send(
					{ url: isEdit ? '/site?action=set_dns_api' : '/site?action=add_dns_api', data: param },
					function (res) {
						bt_tools.msg(res);
						if (res.status) {
							layer.close(indexs);
							if (_that) {
								_that.$refresh_table_list(true);
							} else {
								bt_tools.send({ url: '/site?action=GetDnsApi' }, function (data) {
									site.dns_configured_table = site.data_treating(data);
								});
							}
						}
					},
					isEdit ? 'Modify authentication interface' : 'Add authentication interface'
				);
			},
		});
	},
	/**
	 * 生成不同dns类型的配置
	 * @param {*} type dns|DNSPodDns|AliyunDns|CloudflareDns|GodaddyDns|DNSLADns|
	 * @returns  config 用于重新渲染表单
	 */
	switch_dns_add_key: function (type, isGlobal) {
		// 在原始数据中查找type相同的数据
		var sthat = this,
			firstApi = site.dns_data_treating.find(function (item) {
				return item.name === type;
			}),
			helpObj = {},
			configKey = [];
		for (var i = 0; i < site.dns_interface_list.length; i++) {
			var help = site.dns_interface_list[i].help;
			helpObj[site.dns_interface_list[i].value] = [
				'<a class="btlink" target="_blank" href="' + help[0].link + '">' + help[0].title + '</a>',
				'<a class="btlink" target="_blank" href="' + help[1].link + '">' + help[1].title + '</a>',
			];
		}
		var config = [
			{
				label: lan.site.set_ssl.ver_type,
				group: [
					{
						type: 'select',
						name: 'dns_type',
						width: '330px',
						list: this.dns_interface_list,
						change: function (formData, element, that) {
							// 根据不同的dns接口，渲染不同的输入框
							that.config.form[0].group[0].value = formData.dns_type;
							that.$again_render_form(sthat.switch_dns_add_key(formData.dns_type));
						},
					},
				],
			},
			{
				label: lan.soft.ps,
				group: [
					{
						type: 'text',
						name: 'ps',
						width: '330px',
						placeholder: lan.site.set_ssl.ps_pls,
					},
				],
			},
			{
				group: [
					{
						type: 'help',
						class: 'dns-help',
						list: helpObj[type],
					},
				],
			},
		];
		//高级设置类型追加显示已添加的域名
		if (isGlobal) {
			// 往config的第二个种，追加域名
			config.splice(2, 0, {
				label: lan.site.set_ssl.as_domain,
				group: [
					{
						type: 'textarea',
						name: 'domains',
						style: {
							width: '330px',
							'min-width': '330px',
							'min-height': '130px',
							'line-height': '22px',
							'padding-top': '10px',
							resize: 'both',
						},
						placeholder: lan.site.set_ssl.more_domain_pl,
					},
				],
			});
		}
		$.each(firstApi.add_table[0].fields, function (index, item) {
			configKey.push({
				label: item,
				group: [
					{
						type: 'text',
						name: item,
						width: '330px',
						placeholder: 'Please enter' + item,
					},
				],
			});
		});
		config = config.slice(0, 1).concat(configKey).concat(config.slice(1));
		return config;
	},
	// 深度获取所有dns账号中的域名
	data_treating: function (data) {
		var tableData = [],
			dns_type = [];
		this.dns_data_treating = data.filter(function (item) {
			return item.name !== 'dns';
		}); // 原始数据
		for (var i = 0; i < data.length; i++) {
			if (data[i].name == 'dns') continue; //手动解析
			var item = data[i];
			if (item.data) {
				for (var j = 0; j < item.data.length; j++) {
					tableData.push({
						ps: item.data[j].ps,
						id: item.data[j].id,
						domain: item.data[j].domain,
						conf: item.data[j].conf,
						typeTitle: item.title,
						dns_type: item.name,
						name: item.data[j].conf ? item.data[j].conf[0].value : '',
						value: item.data[j].conf ? item.data[j].conf[1].value : '',
						help: item.help,
						add_table: item.add_table,
					});
				}
			}
			dns_type.push({ title: item.title, value: item.name, help: item.help });
		}
		this.dns_interface_list = dns_type;
		return tableData;
	},
	// 移除dns接口
	remove_dns_interface: function () {
		$('.dns_interface_line.line').remove();
		$('.isdnsbtn').hide();
	},
	// 自动刷新dns域名情况
	refresh_dns_interface: function () {
		// 当前解析类型
		var dns_type = $('select[name=dns_select]').val(),
			that = this;
		// 是否手动解析
		if (dns_type == 'dns') {
			return false;
		}
		bt_tools.send({ url: 'site?action=test_domains_api', data: { domains: JSON.stringify(site.domain_dns_list) } }, function (res) {
			if (site.domain_dns_type == 'one') {
				if ($.isEmptyObject(res[0])) {
					$('.damin_dns_result').html(
						'<div class="btn-group"><button class="btn btn-danger btn-xs dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">DNS interface: Click Configure <span class="caret"></span></button><ul class="dropdown-menu"></ul></div>'
					);
				} else {
					$('.damin_dns_result').html(
						'<div class="btn-group"><button class="btn btn-success btn-xs dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">DNS interface: <span class="dns_selected_interface">' +
							res[0].dns_name +
							'</span><span class="caret"></span></button><ul class="dropdown-menu"></ul></div>'
					);
				}

				// 点击配置
				$('.damin_dns_result').on('click', 'button', function () {
					// 没有dns接口，直接跳转到添加
					if (site.dns_configured_table.length == 0) return site.editDns({ domains: $('#apply_site_name').val() });
					// 渲染dns列表
					var options = '';
					$.each(site.dns_configured_table, function (index, item) {
						options += '<li data-id="' + item.id + '">' + item.typeTitle + '[' + item.ps + ']' + '</a></li>';
					});
					$('.damin_dns_result .dropdown-menu').html(options);
				});
				// 点击选择
				$('.damin_dns_result .dropdown-menu')
					.unbind('click')
					.on('click', 'li', function () {
						var dns_id = $(this).data('id'),
							param = { api_id: dns_id },
							item = site.dns_configured_table.find(function (item) {
								return item.id == dns_id;
							});

						param['dns_type'] = item.dns_type;
						param['force_domain'] = $('#apply_site_name').val();
						bt_tools.send({ url: 'site?action=set_dns_api', data: param }, function (res) {
							that.refresh_dns_interface();
						});
					});
			} else {
				var view = '';
				$.each(site.domain_dns_list, function (index, item) {
					// 是否空对象（没有设置dns）
					var isDnsEmpty = $.isEmptyObject(res[index]);
					view +=
						'<div class="dns_domains_item">\
							<div class="dns_domains_item_title">' +
						item +
						'</div>\
							<div class="dns_domains_item_btn">\
								<div class="btn-group">\
									<button type="button" class="btn btn-' +
						(isDnsEmpty ? 'danger' : 'success') +
						' btn-xs dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">\
									DNS interface: <span class="dns_selected_interface">' +
						(isDnsEmpty ? 'Click Configure' : res[index].dns_name) +
						'</span><span class="caret"></span>\
									</button>\
									<ul class="dropdown-menu">\
									</ul>\
								</div>\
								<div class="dns_domains_item_close">\
									<i class="glyphicon glyphicon-remove"></i>\
								</div>\
							</div>\
						</div>';
				});
				$('.dns_domains_multi_list').html(view);

				// 点击配置
				$('.dns_domains_item_btn button').click(function () {
					// 没有dns接口，直接跳转到添加
					if (site.dns_configured_table.length == 0) return site.editDns({ domains: $(this).parents('.dns_domains_item').find('.dns_domains_item_title').text() });
					// 渲染dns列表
					var options = '';
					$.each(site.dns_configured_table, function (index, item) {
						options += '<li data-id="' + item.id + '">' + item.typeTitle + '[' + item.ps + ']' + '</a></li>';
					});
					$('.dns_domains_item_btn .dropdown-menu').html(options);
				});
				// 点击选择
				$('.dns_domains_item_btn .dropdown-menu')
					.unbind('click')
					.on('click', 'li', function () {
						var dns_id = $(this).data('id'),
							param = { api_id: dns_id },
							item = site.dns_configured_table.find(function (item) {
								return item.id == dns_id;
							});

						param['dns_type'] = item.dns_type;
						param['force_domain'] = $(this).parents('.dns_domains_item').find('.dns_domains_item_title').text();
						bt_tools.send({ url: 'site?action=set_dns_api', data: param }, function (res) {
							that.refresh_dns_interface();
						});
					});
				// 点击删除
				$('.dns_domains_item_close')
					.unbind('click')
					.click(function () {
						// 从site.domain_dns_list中删除当前选中的域名
						var domain = $(this).parents('.dns_domains_item').find('.dns_domains_item_title').text();
						site.domain_dns_list = site.domain_dns_list.filter(function (item) {
							return item != domain;
						});
						$(this).parents('.dns_domains_item').remove();
					});
				// dns_domains_item鼠标经过时添加active，离开时移除active
				$('.dns_domains_item')
					.unbind('mouseenter')
					.mouseenter(function () {
						$(this).addClass('active');
					});
				$('.dns_domains_item')
					.unbind('mouseleave')
					.mouseleave(function () {
						$(this).removeClass('active');
					});
			}
		});
	},
	//批量设置站点证书
	setBathSiteSsl: function (batch_list, callback) {
		bt_tools.send(
			{
				url: '/ssl?action=SetBatchCertToSite',
				data: {
					BatchInfo: JSON.stringify(batch_list),
				},
			},
			function (res) {
				if (callback) callback(res);
			},
			'Set site certificates in batches'
		);
	},
	set_ssl: function (web) {
		//站点/项目名、放置位置
		bt.site.get_site_ssl(web.name, function (rdata) {
			var type = rdata.type; // 类型
			var certificate = rdata.cert_data; // 证书信息
			var pushAlarm = rdata.push; // 是否推送告警
			var isStart = rdata.status; // 是否启用
			var layers = null;
			var expirationTime = certificate.endtime; // 证书过期时间
			var isRenew = (function () {
				// 是否续签
				var state = false;
				if (expirationTime <= 30) state = true;
				if (type === 2 && expirationTime < 0) state = true;
				if (type === 0 || type === -1) state = false;
				return state;
			})();

			// 续签视图
			function renewal_ssl_view(item) {
				bt.confirm(
					{
						title: 'Visa renewal letter',
						msg: 'The current certificate order needs to be regenerated into a new order, which requires manual renewal and re-deployment of the certificate. Do you want to continue?',
					},
					function () {
						var loadT = bt.load(lan.site.set_ssl.renew_cert_load);
						bt.send(
							'renew_cert_order',
							'ssl/renew_cert_order',
							{
								pdata: JSON.stringify({ oid: item.oid }),
							},
							function (res) {
								loadT.close();
								site.reload();
								setTimeout(function () {
									bt.msg(res);
								}, 1000);
							}
						);
					}
				);
			}

			// 申请宝塔证书
			function apply_bt_certificate() {
				var html = '';
				var domains = [];
				for (var i = 0; i < rdata.domain.length; i++) {
					var item = rdata.domain[i];
					if (item.name.indexOf('*') == -1) domains.push({ title: item.name, value: item.name });
				}
				for (var i = 0; i < domains.length; i++) {
					var item = domains[i];
					html += '<option value="' + item.value + '">' + item.title + '</option>';
				}
				bt.open({
					type: 1,
					title: lan.site.set_ssl.req_free_cert,
					area: '610px',
					content:
						'<form class="bt_form perfect_ssl_info free_ssl_info" onsubmit="return false;">\
							<div class="warning_info mb20" style="display: flex;height: 60px;align-items: center;">\
								<span class="glyphicon glyphicon-alert" style="color: #a94442; margin-right: 10px;"></span>\
								<div>提示：尊敬的用户您好，感谢您对宝塔免费SSL证书的支持，由于证书签发机制的调整，我们的免费SSL证书签发将于<b>2023年12月31日</b>进行下架，<a target="_blank" class="btlink" href="https://www.trustasia.com/view-free-ssl-one-year-adjustment-announcement/">查看详情</a>。</div>\
							</div>\
							<div class="line">\
									<span class="tname">' +
						lan.site.set_ssl.cert_info +
						'</span>\
									<div class="info-r">\
											<span class="ssl_title">TrustAsia TLS RSA CA(Free edition)</span>\
									</div>\
							</div>\
							<div class="line">\
									<span class="tname">' +
						lan.site.set_ssl.domain_name +
						'</span>\
									<div class="info-r"><select class="bt-input-text mr5 " name="domain" style="width:200px">' +
						html +
						'</select></div>\
							</div>\
							<div class="line">\
									<span class="tname">' +
						lan.site.set_ssl.per_name +
						'</span>\
									<div class="info-r">\
											<input type="text" class="bt-input-text mr5" name="orgName" value="" placeholder="' +
						lan.site.set_ssl.per_name_pl +
						'" />\
									</div>\
							</div>\
							<div class="line">\
									<span class="tname">' +
						lan.site.set_ssl.lo_area +
						'</span>\
									<div class="info-r">\
											<input type="text" class="bt-input-text mr5" name="orgRegion" value="" placeholder="' +
						lan.site.set_ssl.province_pl +
						'" style="width: 190px; margin-right:0;" >\
											<input type="text" class="bt-input-text mr5" name="orgCity" value="" placeholder="' +
						lan.site.set_ssl.city_pl +
						'" style="width: 190px; margin-left: 15px;"  />\
									</div>\
							</div>\
							<div class="line">\
									<span class="tname">' +
						lan.site.set_ssl.address +
						'</span>\
									<div class="info-r">\
											<input type="text" class="bt-input-text mr5" name="orgAddress" value="" placeholder="' +
						lan.site.set_ssl.address_pl +
						'" />\
									</div>\
							</div>\
							<div class="line">\
									<span class="tname">' +
						lan.public_backup.mobile_phone_or_email +
						'</span>\
									<div class="info-r">\
											<input type="text" class="bt-input-text mr5" name="orgPhone" value="" placeholder="' +
						lan.site.set_ssl.phone_pl +
						'" />\
									</div>\
							</div>\
							<div class="line">\
									<span class="tname">' +
						lan.site.set_ssl.pos_code +
						'</span>\
									<div class="info-r">\
											<input type="text" class="bt-input-text mr5" name="orgPostalCode" value="" placeholder="' +
						lan.site.set_ssl.pos_code_pl +
						'" />\
									</div>\
							</div>\
							<div class="line" style="display:none;">\
									<span class="tname">' +
						lan.site.set_ssl.section +
						'</span>\
									<div class="info-r">\
											<input type="text" class="bt-input-text mr5" name="orgDivision" value="' +
						lan.site.set_ssl.g_a +
						'"/>\
									</div>\
							</div>\
							<div class="line">\
									<span class="tname"></span>\
									<div class="info-r">\
											<span style="line-height: 20px;color:red;display: inline-block;">' +
						lan.site.set_ssl.add_tips +
						'</span>\
									</div>\
							</div>\
							<div class="line">\
									<div class="info-r"><button class="btn btn-success submit_ssl_info">' +
						lan.site.set_ssl.sub_info +
						'</button></div>\
							</div>\
					</form>',
					success: function (layero, index) {
						$('.submit_ssl_info').click(function () {
							var form = $('.free_ssl_info').serializeObject();
							for (var key in form) {
								if (Object.hasOwnProperty.call(form, key)) {
									var value = form[key],
										el = $('[name="' + key + '"]');
									if (value == '') {
										layer.tips(el.attr('placeholder'), el, { tips: ['1', 'red'] });
										el.focus();
										el.css('borderColor', 'red');
										return false;
									} else {
										el.css('borderColor', '');
									}
									switch (key) {
										case 'orgPhone':
											if (!bt.check_phone(value)) {
												layer.tips(lan.site.set_ssl.phone_ver, el, { tips: ['1', 'red'] });
												el.focus();
												el.css('borderColor', 'red');
												return false;
											}
											break;
										case 'orgPostalCode':
											if (!/^[0-9]\d{5}(?!\d)$/.test(value)) {
												layer.tips(lan.site.set_ssl.postal_ver, el, { tips: ['1', 'red'] });
												el.focus();
												el.css('borderColor', 'red');
												return false;
											}
											break;
									}
								}
							}
							if (form.domain.indexOf('www.') != -1) {
								var rootDomain = form.domain.split(/www\./)[1];
								if (!$.inArray(domains, rootDomain)) {
									layer.msg(lan.site.set_ssl.no_root_tip(form.domain, rootDomain), { icon: 2, time: 5000 });
									return;
								}
							}
							var loadT = bt.load(lan.site.set_ssl.sub_cert);
							bt.send('ApplyDVSSL', 'ssl/ApplyDVSSL', $.extend(form, { path: web.path }), function (tdata) {
								loadT.close();
								if (tdata.msg.indexOf('<br>') != -1) {
									layer.msg(tdata.msg, { time: 0, shadeClose: true, area: '600px', icon: 2, shade: 0.3 });
								} else {
									bt.msg(tdata);
								}
								if (tdata.status) {
									layer.close(index);
									site.ssl.verify_domain(tdata.data.partnerOrderId, web.name);
								}
							});
						});
						$('.free_ssl_info input').keyup(function (res) {
							var value = $(this).val();
							if (value == '') {
								layer.tips($(this).attr('placeholder'), $(this), { tips: ['1', 'red'] });
								$(this).focus();
								$(this).css('borderColor', 'red');
							} else {
								$(this).css('borderColor', '');
							}
						});
					},
				});
			}

			if (!Array.isArray(certificate.dns)) certificate = { dns: [] };

			$('#webedit-con').html(
				'<div class="warning_info mb10 ' +
					(!isRenew && isStart ? 'hide' : '') +
					'">' +
					'<p class="' +
					(isStart ? 'hide' : '') +
					'">' +
					lan.site.set_ssl.tips1 +
					'<button class="btn btn-success btn-xs ml10 cutTabView">' +
					lan.site.set_ssl.apply +
					'</button></p>' +
					'<p class="' +
					(isRenew && isStart ? '' : 'hide') +
					'">' +
					lan.site.set_ssl.tips2(
						'<span class="ellipsis_text" style="display: inline-block;vertical-align:bottom;max-width: 250px;width: auto;" title="' +
							certificate.dns.join(', ') +
							'">' +
							certificate.dns.join(', ') +
							'</span>',
						expirationTime < 0
					) +
					'<button class="btn btn-success btn-xs mlr15 renewCertificate" data-type="' +
					rdata.type +
					'">' +
					lan.site.set_ssl.renewal +
					'</button></p>' +
					'</div>' +
					'<div id="ssl_tabs"></div><div class="tab-con" style="padding:10px 0;"></div>'
			);
			var tabs = [
				{
					title: lan.site.set_ssl.menu1 + ' - <i class="' + (rdata.status ? 'btlink' : 'bterror') + '">[' + (rdata.status ? lan.site.set_ssl.deployed : lan.site.set_ssl.not_deployed) + ']</i>',
					callback: function (content) {
						acme.id = web.id;
						var classify = '';
						var typeList = [lan.site.set_ssl.cert_type1, lan.site.set_ssl.cert_type2, lan.site.set_ssl.cert_type3, lan.site.set_ssl.cert_type4];
						var state = $(
							'<div class="ssl_state_info ' +
								(!rdata.csr ? 'hide' : '') +
								'">' +
								'<div class="state_info_flex">' +
								'<div class="state_item"><span>' +
								lan.site.set_ssl.cert_type +
								':</span><span><a href="javascript:;" class="btlink cutSslType" data-type="' +
								(typeList[rdata.type] === lan.site.other_cert ? -1 : rdata.type) +
								'">' +
								(rdata.type === -1 ? lan.site.set_ssl.other_cert : typeList[rdata.type]) +
								'</a></span></div>' +
								'<div class="state_item"><span>' +
								lan.site.set_ssl.cert_brand +
								':</span><span class="ellipsis_text" title="' +
								certificate.issuer +
								'">' +
								certificate.issuer +
								'</span></div>' +
								'</div>' +
								'<div class="state_info_flex">' +
								'<div class="state_item"><span>' +
								lan.site.set_ssl.auth_domain +
								'</span><span class="ellipsis_text" title="' +
								certificate.dns.join('、') +
								'">' +
								certificate.dns.join('、') +
								'</span></div>' +
								'<div class="state_item"><span>' +
								lan.site.set_ssl.expire_time +
								'</span><span style="' +
								(expirationTime >= 30 ? '' : 'color:#EF0808') +
								'" class="' +
								(expirationTime >= 30 ? 'btlink' : '') +
								'">' +
								(expirationTime >= 0 ? lan.site.set_ssl.expire_time_text(rdata.cert_data.notAfter, expirationTime.toFixed(0)) : lan.site.set_ssl.expired) +
								'</span></div>' +
								'</div>' +
								'<div class="state_info_flex">' +
								'<div class="state_item"><span>' +
								lan.site.set_ssl.force_https +
								'</span><span><span class="bt_switch"><input class="btswitch btswitch-ios" id="https" type="checkbox" ' +
								(rdata.httpTohttps ? 'checked' : '') +
								'><label class="btswitch-btn" for="https"></label></span></span></div>' +
								// '<div class="state_item"><span>' + lan.site.set_ssl.expire_reminder + ':</span><span><span class="bt_switch"><input class="btswitch btswitch-ios" id="expiration" type="checkbox" ' +
								// (pushAlarm.status ? 'checked' : '') +
								// '><label class="btswitch-btn" for="expiration"></label></span><a class="btlink setAlarmMode" style="margin-left: 15px;" href="javascript:;">Config</a></span></div>' +
								'</div>' +
								'</div>' +
								'<div class="custom_certificate_info">' +
								'<div class="state_item"><span>' +
								lan.site.set_ssl.ssl_key +
								'</span><textarea class="bt-input-text key" name="key">' +
								(rdata.key || '') +
								'</textarea></div>' +
								'<div class="state_item"><span>' +
								lan.site.set_ssl.ssl_crt +
								'</span><textarea class="bt-input-text key" name="csr">' +
								(rdata.csr || '') +
								'</textarea></div>' +
								'</div>' +
								'<div class="mt10">' +
								'<button type="button" class="btn btn-success btn-sm mr10 saveCertificate ' +
								(isStart ? '' : '') +
								'">' +
								(isStart ? lan.site.set_ssl.save_btn : lan.site.set_ssl.save_enable_btn) +
								'</button>' +
								'<button type="button" class="btn btn-success btn-sm mr10 renewCertificate ' +
								(isRenew || type === 1 ? '' : 'hide') +
								'" data-type="' +
								rdata.type +
								'">' +
								lan.site.set_ssl.renewal_btn +
								'</button>' +
								'<button type="button" class="btn btn-default btn-sm mr10 downloadCertificate ' +
								(!rdata.csr ? 'hide' : 'hide') +
								'">' +
								lan.site.set_ssl.download_btn +
								'</button>' +
								'<button type="button" class="btn btn-default btn-sm closeCertificate ' +
								(!isStart ? 'hide' : '') +
								'">' +
								lan.site.set_ssl.close_btn +
								'</button>' +
								'</div>'
						);
						content.append(state);
						content.append(
							bt.render_help([lan.site.set_ssl.save_ssl_tips1, lan.public_backup.cret_err, lan.public_backup.pem_format, lan.site.set_ssl.save_ssl_tips2, lan.site.set_ssl.save_ssl_tips3])
						);
						// if(rdata.status) {
						// 	bt_tools.send({url: '/site?action=check_ssl',data: {hostname: web.name}}, function (res) {
						// 		if(!res.status) content.prepend('<div class="div-box-tips"><i class="ico-text-hint"></i><span>'+ res.msg +'<span></div>')
						// 	},{verify:false})
						// }
						var setAlarmMode = bt.get_cookie('setAlarmMode');
						if (!pushAlarm.status && rdata.csr && !setAlarmMode) {
							// if (true) {
							bt.set_cookie('setAlarmMode', 1);
							layer.tips(lan.site.set_ssl.set_alarm_mode_tips, '.setAlarmMode', {
								tips: [1, '#d9534f'],
								area: '380px',
								time: 5000,
							});
							setTimeout(function () {
								$(window).one('click', function () {
									layer.closeAll('tips');
								});
							}, 500);
						}
						var moduleConfig = null;
						function cacheModule(callback) {
							if (moduleConfig && callback) return callback(moduleConfig);
							bt.site.get_module_config({ name: 'site_push', type: 'ssl' }, function (rdata1) {
								moduleConfig = rdata1;
								if (callback) callback(rdata1);
							});
						}

						/**
						 * 提醒到期弹框
						 * @param $check 到期提醒开关
						 */
						function alarmMode($check) {
							var time = new Date().getTime();
							var isExpiration = pushAlarm.status;
							if ($check) isExpiration = $check.is(':checked');
							layer.open({
								type: 1,
								title: lan.site.set_ssl.expire_reminder_title,
								area: '470px',
								closeBtn: 2,
								content:
									'\
									<div class="pd20">\
										<div class="bt-form">\
											<div class="line">\
												<span class="tname">' +
									lan.site.set_ssl.expire_reminder +
									'</span>\
												<div class="info-r line-switch">\
													<input type="checkbox" id="dueAlarm" class="btswitch btswitch-ios" name="due_alarm" ' +
									(isExpiration ? 'checked="checked"' : '') +
									' />\
													<label class="btswitch-btn" for="dueAlarm"></label>\
												</div>\
											</div>\
											<div class="line">\
												<span class="tname">' +
									lan.site.set_ssl.site +
									'</span>\
												<div class="info-r">\
													<input class="bt-input-text mr10" disabled style="width:200px;" value="' +
									web.name +
									'" />\
												</div>\
											</div>\
											<div class="line">\
												<span class="tname">' +
									lan.site.set_ssl.remaining_days +
									'</span>\
												<div class="info-r">\
													<div class="inlineBlock">\
														<input type="number" min="1" name="cycle" class="bt-input-text triggerCycle" style="width:70px;" value="' +
									(pushAlarm.cycle || '30') +
									'" />\
														<span class="unit">Days</span>\
													</div>\
												</div>\
											</div>\
											<div class="line">\
												<span class="tname">' +
									lan.site.set_ssl.number_ransmissions +
									'</span>\
												<div class="info-r">\
													<div class="inlineBlock">\
														<input type="number" min="1" name="push_count" class="bt-input-text triggerPushCount" style="width:70px;" value="' +
									(pushAlarm.push_count || '2') +
									'" />\
														<span class="unit">，' +
									lan.site.set_ssl.no_more +
									'</span>\
													</div>\
												</div>\
											</div>\
											<div class="line">\
												<span class="tname">' +
									lan.site.set_ssl.notification_mode +
									'</span>\
												<div class="info-r installPush"></div>\
											</div>\
											<div class="line">\
												<span class="tname">' +
									lan.site.set_ssl.application_config +
									'</span>\
												<div class="info-r">\
													<div class="inlineBlock module-check setAllSsl">\
														<div class="cursor-pointer form-checkbox-label mr10">\
															<i class="form-checkbox cust—checkbox cursor-pointer mr5"></i>\
															<input type="checkbox" class="form—checkbox-input hide mr10" name="allSsl"/>\
															<span class="vertical_middle">' +
									lan.site.set_ssl.apply_all +
									'<span class="red">&nbsp;' +
									lan.site.set_ssl.no_config_site +
									'</span></span>\
														</div>\
													</div>\
												</div>\
											</div>\
										</div>\
									</div>',
								btn: [lan.site.set_ssl.save_config, lan.public.cancel],
								success: function ($layer) {
									cacheModule(function (rdata1) {
										// 获取配置
										bt.site.get_msg_configs(function (rdata) {
											var html = '',
												unInstall = '',
												pushList = rdata1.push;
											for (var key in rdata) {
												var item = rdata[key],
													_html = '',
													accountConfigStatus = false,
													module = pushAlarm.module || [];
												if (pushList.indexOf(item.name) === -1) continue;
												if (key == 'sms') continue;
												if (key === 'wx_account') {
													if (!$.isEmptyObject(item.data) && item.data.res.is_subscribe && item.data.res.is_bound) {
														accountConfigStatus = true; //安装微信公众号模块且绑定
													}
												}
												_html =
													'<div class="inlineBlock module-check ' +
													(!item.setup || $.isEmptyObject(item.data) ? 'check_disabled' : key == 'wx_account' && !accountConfigStatus ? 'check_disabled' : '') +
													'">' +
													'<div class="cursor-pointer form-checkbox-label mr10">' +
													'<i class="form-checkbox cust—checkbox cursor-pointer mr5 ' +
													(module.indexOf(item.name) > -1 ? (!item.setup || $.isEmptyObject(item.data) ? '' : key == 'wx_account' && !accountConfigStatus ? '' : 'active') : '') +
													'" data-type="' +
													item.name +
													'"></i>' +
													'<input type="checkbox" class="form—checkbox-input hide mr10" name="' +
													item.name +
													'" ' +
													(item.setup || !$.isEmptyObject(item.data) ? (key == 'wx_account' && !accountConfigStatus ? '' : 'checked') : '') +
													'/>' +
													'<span class="vertical_middle" title="' +
													item.ps +
													'">' +
													item.title +
													(!item.setup || $.isEmptyObject(item.data)
														? '[<a target="_blank" class="bterror installNotice" data-type="' + item.name + '">' + lan.public_backup.install + '</a>]'
														: key == 'wx_account' && !accountConfigStatus
														? '[<a target="_blank" class="bterror installNotice" data-type="' + item.name + '">' + lan.public_backup.install + '</a>]'
														: '') +
													'</span>' +
													'</div>' +
													'</div>';
												if (!item.setup) {
													unInstall += _html;
												} else {
													html += _html;
												}
											}
											$('.installPush').html(html + unInstall);
											$('.setAllSsl').on('click', function () {
												var that = $(this).find('i');
												if (that.hasClass('active')) {
													that.removeClass('active');
													that.next().prop('checked', false);
												} else {
													that.addClass('active');
													that.next().prop('checked', true);
												}
											});
											if (pushAlarm.project === 'all' && pushAlarm.status) $('.setAllSsl').trigger('click');
										});
									});

									// 安装消息通道
									$('.installPush').on('click', '.form-checkbox-label', function () {
										var that = $(this).find('i');
										if (!that.parent().parent().hasClass('check_disabled')) {
											if (that.hasClass('active')) {
												that.removeClass('active');
												that.next().prop('checked', false);
											} else {
												that.addClass('active');
												that.next().prop('checked', true);
											}
										}
									});
									$('.triggerCycle').on('input', function () {
										$('.siteSslHelp span').html($(this).val());
									});

									$('.installPush').on('click', '.installNotice', function () {
										var type = $(this).data('type');
										openAlertModuleInstallView(type);
									});
								},
								yes: function (index) {
									var status = $('input[name="due_alarm"]').is(':checked');
									var cycle = $('.triggerCycle').val();
									var push_count = $('.triggerPushCount').val();
									var arry = [];
									var module = '';
									var isAll = $('[name="allSsl"]').is(':checked');
									$('.installPush .active').each(function (item) {
										var item = $(this).attr('data-type');
										arry.push(item);
									});
									if (!arry.length) return layer.msg('Please select an alarm mode', { icon: 2 });
									if (!parseInt(cycle)) return layer.msg('Remaining days cannot be less than 1', { icon: 2 });
									if (!parseInt(push_count)) return layer.msg('Send times cannot be less than 1', { icon: 2 });

									// 参数
									var data = {
										status: status,
										type: 'ssl',
										project: web.name,
										cycle: parseInt(cycle),
										title: 'Website SSL expiration alert',
										module: arry.join(','),
										interval: 600,
										push_count: parseInt(push_count),
									};

									// 判断是否点击全局应用
									if (isAll) {
										// 请求设置全局应用告警配置
										var allData = Object.assign({}, data);
										allData.status = true;
										allData.project = 'all';
										bt.site.set_push_config({
											name: 'site_push',
											id: time,
											data: JSON.stringify(allData),
										});
									}

									// 请求设置本站点告警配置
									bt.site.set_push_config(
										{
											name: 'site_push',
											id: pushAlarm.id ? pushAlarm.id : time,
											data: JSON.stringify(data),
										},
										function (rdata) {
											bt.msg(rdata);
											setTimeout(function () {
												site.reload();
											}, 1000);
											layer.close(index);
										}
									);
								},
								cancel: function () {
									$check && $check.prop('checked', !isExpiration);
								},
								btn2: function () {
									$check && $check.prop('checked', !isExpiration);
								},
							});
						}
						// 设置强制HTTPS
						$('#https').on('click', function () {
							var that = $(this),
								isHttps = $(this).is(':checked');
							if (!isHttps) {
								layer.confirm(
									lan.site.set_ssl.force_https_confirm,
									{
										icon: 3,
										closeBtn: 2,
										title: 'Turn off forced HTTPS',
										cancel: function () {
											that.prop('checked', !isHttps);
										},
										btn2: function () {
											that.prop('checked', !isHttps);
										},
									},
									function () {
										bt.site.close_http_to_https(web.name, function (rdata) {
											if (rdata.status) {
												setTimeout(function () {
													site.reload(7);
												}, 3000);
											} else {
												that.prop('checked', !isHttps);
											}
										});
									}
								);
							} else {
								bt.site.set_http_to_https(web.name, function (rdata) {
									if (rdata.status) {
										site.reload(7);
									} else {
										that.prop('checked', !isHttps);
										layer.confirm(lan.site.set_ssl.open_ssl_comfirm, { icon: 3, title: 'Tips' }, function (index) {
											$.ajaxSettings.async = false;
											$('.saveCertificate').click();
											$.ajaxSettings.async = true;
											$('#https').click();
											layer.close(index);
										});
									}
								});
							}
						});

						// 设置告警通知
						$('#expiration').on('click', function () {
							layer.close(layers);
							var _that = $(this);
							var isExpiration = $(this).is(':checked');
							var time = new Date().getTime();
							if (isExpiration) {
								alarmMode(_that);
							} else {
								var data = JSON.stringify({
									status: isExpiration,
									type: 'ssl',
									project: web.name,
									cycle: parseInt(pushAlarm.cycle),
									title: 'Website SSL expiration alert',
									module: pushAlarm.module,
									interval: 600,
									push_count: 1,
								});
								var id = pushAlarm.id ? pushAlarm.id : time;
								if (pushAlarm.project === 'all') id = time;
								bt.site.set_push_config(
									{
										name: 'site_push',
										id: id,
										data: data,
									},
									function (rdata) {
										bt.msg(rdata);
										setTimeout(function () {
											site.reload();
										}, 1000);
									}
								);
							}
						});

						// 保存证书
						$('.saveCertificate').on('click', function () {
							var key = $('[name="key"]').val(),
								csr = $('[name="csr"]').val();
							function set_ssl() {
								if (key === '' || csr === '') return bt.msg({ status: false, msg: 'Please fill in the complete certificate content' });
								bt.site.set_ssl(
									web.name,
									{
										type: rdata.type,
										siteName: rdata.siteName,
										key: key,
										csr: csr,
									},
									function (ret) {
										if (ret.status) site.reload(7);
										if (site.model_table) site.model_table.$refresh_table_list(true);
										if (node_table) node_table.$refresh_table_list(true);
										if (site_table) site_table.$refresh_table_list(true);
										bt.msg(ret);
									}
								);
							}

							if ((key !== rdata.key && rdata.key) || (csr !== rdata.csr && rdata.key)) {
								layer.confirm(
									lan.site.set_ssl.edit_cert_comfirm,
									{
										icon: 3,
										closeBtn: 2,
										title: 'Certificate saving prompt',
									},
									set_ssl
								);
							} else {
								set_ssl();
							}
						});

						// 告警方式
						$('.setAlarmMode').on('click', function () {
							layer.close(layers);
							alarmMode();
						});

						// 续签证书
						$('.renewCertificate')
							.unbind('click')
							.on('click', function () {
								var type = parseInt($(this).attr('data-type'));
								switch (type /**/) {
									case 3: // 商业证书续签
										renewal_ssl_view({ oid: rdata.oid });
										break;
									case 2: // 宝塔证书 续签
										apply_bt_certificate();
										layer.msg('The current certificate type does not support one-click renewal. Please fill in the information application again', { icon: 2, time: 2000 });
										break;
									case 1: // Let's Encrypt 续签
										site.ssl.renew_ssl(web.name, rdata.auth_type, rdata.index);
										break;
								}
							});

						// 关闭证书
						$('.closeCertificate').on('click', function () {
							site.ssl.set_ssl_status('CloseSSLConf', web.name);
						});

						// 切换证书类型
						$('.cutSslType').on('click', function () {
							var type = $(this).attr('data-type');
							switch (type) {
								case '0':
									type = 0;
									break;
								case '1':
									type = 3;
									break;
								case '2':
									type = 2;
									break;
								case '3':
									type = 1;
									break;
							}
							$('#ssl_tabs span:eq(' + type + ')').trigger('click');
						});

						// 下载证书
						$('.downloadCertificate').on('click', function () {
							var key = $('[name="key"]').val(),
								pem = $('[name="csr"]').val();
							bt.site.download_cert(
								{
									siteName: web.name,
									pem: pem,
									key: key,
								},
								function (rdata) {
									if (rdata.status) {
										window.open('/download?filename=' + encodeURIComponent(rdata.msg));
									} else {
										layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
									}
								}
							);
						});
					},
				},
				{
					title: lan.site.set_ssl.menu2 + '<i class="ssl_recom_icon"></i>',
					callback: function (robj) {
						$.getScript('https://js.stripe.com/v3/');
						robj = $('#webedit-con .tab-con');
						bt.pub.get_user_info(function (udata) {
							if (udata.status) {
								var deploy_ssl_info = rdata,
									html = '',
									deploy_html = '',
									product_list,
									userInfo,
									order_list,
									is_check = true,
									itemData,
									activeData,
									loadY,
									pay_ssl_layer;
								bt.send('get_order_list', 'ssl/get_order_list', {}, function (res) {
									var rdata = res.res;
									order_list = rdata;
									if (rdata.length == 0) {
										$('#ssl_order_list tbody').html(
											'<tr><td colspan="5" style="text-align:center;">' +
												lan.site.set_ssl.no_cert +
												' <a class="btlink" href="javascript:$(\'.ssl_business_application\').click();"> ->' +
												lan.site.set_ssl.apply_certificate +
												'</a></td></tr>'
										);
										return;
									}
									$.each(rdata, function (index, item) {
										if (deploy_ssl_info.type == 3 && deploy_ssl_info.oid === item.uc_id) {
											deploy_html +=
												'<tr data-index="' +
												index +
												'">' +
												'<td><span>' +
												item.domains.join('、') +
												'</span></td><td><span class="size_ellipsis" title="' +
												item.title +
												'" style="width:110px;display:block;">' +
												item.title +
												'</span></td><td>' +
												(function () {
													var dayTime = new Date().getTime() / 1000,
														color = '',
														endTiems = '';
													if (item.end_date != '') {
														item.end_date = parseInt(item.end_date);
														endTiems = parseInt((item.end_date - dayTime) / 86400);
														if (endTiems <= 15) color = 'orange';
														if (endTiems <= 7) color = 'red';
														if (endTiems < 0) return '<span style="color:red">' + lan.site.set_ssl.expired + '</span>';
														return '<span style="' + color + '">' + lan.site.set_ssl.expire_date_text(endTiems) + '</span>';
													} else {
														return '--';
													}
												})() +
												'</td><td>' +
												lan.site.set_ssl.order_complate +
												'</td><td style="text-align:right">' +
												lan.site.set_ssl.deployed +
												' | <a class="btlink" href="javascript:site.ssl.set_ssl_status(\'CloseSSLConf\',\'' +
												web.name +
												'\',2)">' +
												lan.public.close +
												'</a></td></td>';
										} else {
											html +=
												'<tr data-index="' +
												index +
												'">' +
												'<td><span>' +
												(item.domains == null ? '--' : item.domains.join('、')) +
												'</span></td><td><span class="size_ellipsis" title="' +
												item.title +
												'" style="width:110px;display:block;">' +
												item.title +
												'</span></td><td>' +
												(function () {
													var dayTime = new Date().getTime() / 1000,
														color = '',
														endTiems = '';
													if (item.end_date != '') {
														item.end_date = parseInt(item.end_date);
														endTiems = parseInt((item.end_date - dayTime) / 86400);
														if (endTiems <= 15) color = 'orange';
														if (endTiems <= 7) color = 'red';
														if (endTiems < 0) return '<span style="color:red">' + lan.site.set_ssl.expired + '</span>';
														return '<span style="' + color + '">' + lan.site.set_ssl.expire_date_text(endTiems) + '</span>';
													} else {
														return '--';
													}
												})() +
												'</td><td>' +
												(function () {
													var suggest = '';
													if (!item.install)
														suggest =
															'&nbsp;|<span class="bt_ssl_suggest" style="display: inline-block;white-space: nowrap;"><span>' +
															lan.site.set_ssl.troubleshooting_method +
															'?</span><div class="suggest_content"><ul style="display:flex;"><li>' +
															lan.site.set_ssl.check_oneself +
															'<p style="white-space: pre-wrap;">' +
															lan.site.set_ssl.check_self_tip +
															'</p><div><a class="btlink" style="white-space: pre-wrap;" href="https://www.aapanel.com/forum/d/19277-business-ssl-certificate-tutorial" target="_blank">' +
															lan.site.set_ssl.how_verify +
															'?</a></div></li><li style="position: relative;padding-left: 15px;">Labor Service Purchase<p style="white-space: pre-wrap;">Need deployment assistance? Human customer service available.</p><div><button class="btn btn-success btn-xs btn-title service_buy" type="button" data-oid="' +
															item.uc_id +
															'">Buy</button></div></li>' +
															'</ul></div></span>';
													if (item.certId == '') {
														return '<span style="color:orange;cursor: pointer;" class="options_ssl" data-type="perfect_user_info">' + lan.site.set_ssl.data_com + '</span>' + suggest;
													} else if (item.status === 1) {
														switch (item.order_status) {
															case 'COMPLETE':
																return '<span style="color:#20a53a;">' + lan.site.set_ssl.order_complate + '</span>';
																break;
															case 'PENDING':
																return '<span style="color: orange;">' + lan.site.set_ssl.in_verify + '</span>' + suggest;
																break;
															case 'CANCELLED':
																return '<span style="color: #888;">' + lan.site.set_ssl.cancelled + '</span>';
																break;
															case 'FAILED':
																return '<span style="color:red;">' + lan.site.set_ssl.app_fail + '</span>';
																break;
															default:
																return '<span style="color: orange;">' + lan.site.set_ssl.to_verified + '</span>';
																break;
														}
													} else {
														switch (item.status) {
															case 0:
																return '<span style="color: orange;">' + lan.site.set_ssl.no_pay + '</span>';
																break;
															case -1:
																return '<span style="color: #888;">' + lan.site.set_ssl.cancelled + '</span>';
																break;
															default:
																return '<span>--</span>';
														}
													}
												})() +
												'</td><td style="text-align:right;">' +
												(function () {
													var html = '';
													if (item.renew) html += '<a href="javascript:;" class="btlink options_ssl" data-type="renewal_ssl">' + lan.site.set_ssl.renew_cert + '</a>&nbsp;&nbsp;|&nbsp;&nbsp;';
													if (item.certId == '') {
														// if (item.install) html += '<a class="btlink options_ssl service_method" target="_blank">人工服务</a>&nbsp;|&nbsp;';
														html += '<a href="javascript:;" class="btlink options_ssl"  data-type="perfect_user_info">' + lan.site.set_ssl.complete_data + '</a>';
														return html;
													} else if (item.status === 1) {
														var html = '';
														switch (item.order_status) {
															case 'COMPLETE': //申请成功
																return (
																	'<a href="javascript:;" data-type="deploy_ssl" class="btlink options_ssl">' +
																	lan.site.set_ssl.deploy +
																	'</a>&nbsp;&nbsp;|&nbsp;&nbsp;<a href="/ssl?action=download_cert&uc_id=' +
																	item.uc_id +
																	'" data-type="download_ssl" class="btlink options_ssl" style="white-space: nowrap;">' +
																	lan.site.set_ssl.download +
																	'</a>'
																);
																break;
															case 'PENDING': //申请中
																// if (item.install) html += '<a class="btlink options_ssl service_method" target="_blank">人工服务</a>&nbsp;|&nbsp;';
																html += '<a href="javascript:;" data-type="verify_order" class="btlink options_ssl">' + lan.site.set_ssl.verify + '</a>';
																return html;
																break;
															case 'CANCELLED': //已取消
																return lan.site.set_ssl.no_action;
																break;
															case 'FAILED':
																return '<a href="javascript:;" data-type="info_order" class="btlink options_ssl">' + lan.site.set_ssl.detail + '</a>';
																break;
															default:
																// if (item.install) html += '<a class="btlink options_ssl service_method" target="_blank">人工服务</a>&nbsp;|&nbsp;';
																html += '<a href="javascript:;" data-type="verify_order" class="btlink options_ssl">' + lan.site.set_ssl.verify + '</a>';
																return html;
																break;
														}
													} else {
														return '<span>--</span>';
													}
												})() +
												'</td>' +
												'</tr>';
										}
									});
									$('#ssl_order_list tbody').html(deploy_html + html);
									//解决方案事件
									$('#ssl_order_list').on('click', '.bt_ssl_suggest', function (e) {
										var $this = $(this);
										var $layer = $this.parents('.layui-layer');
										var $cont = $this.find('.suggest_content');
										var rect = $this.offset();
										var layerRect = $layer.offset();
										var top = rect.top - layerRect.top + $this.height() + 7;
										var left = rect.left - layerRect.left - 153;
										$cont.css({
											top: top + 'px',
											left: left + 'px',
											right: 'auto',
											bottom: 'auto',
											width: '410px',
										});
										$('.suggest_content').hide();
										$cont.show();
										$(document).one('click', function () {
											$cont.hide();
										});
										e.stopPropagation();
									});
									// 表格滚动隐藏解决方案内容
									$('.ssl_order_list').scroll(function (e) {
										$('.suggest_content').hide();
									});
									//人工客服购买
									$('#ssl_order_list').on('click', '.service_buy', function () {
										var loads = bt.load('Payment order is being generated, please wait...');
										bt.send(
											'apply_cert_install_pay',
											'ssl/apply_cert_install_pay',
											{
												uc_id: $(this).data('oid'),
											},
											function (res) {
												loads.close();
												if (!res.success) {
													layer.msg(res.res, { icon: 2 });
													return;
												}
												var stripe = Stripe(res.res.stripe_public_key);
												stripe.redirectToCheckout({ sessionId: res.res.session_id });
												// if (res.status != undefined && !res.status) {
												// 	return layer.msg(res.msg, { time: 0, shadeClose: true, icon: 2, shade: 0.3 });
												// }
												// open_service_buy(res);
											}
										);
									});

									//人工客服咨询
									$('.service_method').click(function () {
										bt.onlineService();
									});
								});
								robj.append(
									'<div class="alert alert-success" style="padding: 10px 15px;"><div class="business_line" ><div class="business_info business_advantage" style="padding-top:0"><div class="business_advantage_item"><span class="advantage_icon glyphicon glyphicon glyphicon-ok"></span><span class="advantage_title">' +
										lan.site.set_ssl.enterprise_certificate +
										'</span></div><div class="business_advantage_item"><span class="advantage_icon glyphicon glyphicon glyphicon-ok"></span><span class="advantage_title">' +
										lan.site.set_ssl.exceptional_application +
										'</span></div><div class="business_advantage_item"><span class="advantage_icon glyphicon glyphicon glyphicon-ok"></span><span class="advantage_title">' +
										lan.site.set_ssl.anti_hijackingTampering +
										'</span></div><div class="business_advantage_item"><span class="advantage_icon glyphicon glyphicon glyphicon-ok"></span><span class="advantage_title">' +
										lan.site.set_ssl.increase_seo +
										'</span></div><div class="business_advantage_item"><span class="advantage_icon glyphicon glyphicon glyphicon-ok"></span><span class="advantage_title">' +
										lan.site.set_ssl.indemnity_guarantee +
										'</span></div><div class="business_advantage_item"><span class="advantage_icon glyphicon glyphicon glyphicon-ok"></span><span class="advantage_title">' +
										lan.site.set_ssl.refund_failure +
										'</span></div><div class="business_advantage_item" style="width:60%"><span class="advantage_icon glyphicon glyphicon glyphicon-ok"></span><span class="advantage_title">' +
										lan.site.set_ssl.official_use +
										'</span></div></div></div></div>\
																		<div class= "mtb10" >\
																		<button class="btn btn-success btn-sm btn-title ssl_business_application" type="button">' +
										lan.site.set_ssl.apply_certificate +
										'</button>\
																		<div class="divtable mtb10 ssl_order_list"  style="height: 216px; overflow-y: auto;">\
																				<table class="table table-hover" id="ssl_order_list" style="table-layout: fixed;">\
																						<thead><tr><th width="130px">' +
										lan.public_backup.domain +
										'</th><th  width="110px">' +
										lan.site.set_ssl.certificate_type +
										'</th><th>' +
										lan.site.set_ssl.expire_date +
										'</th><th style="width:130px;">' +
										lan.public.status +
										'</th><th style="text-align:right;width:140px;">' +
										lan.public.action +
										'</th></tr></thead>\
																						<tbody><tr><td colspan="5" style="text-align:center"><img src="/static/images/loading-2.gif" style="width:15px;vertical-align: middle;"><span class="ml5" style="vertical-align: middle;">' +
										lan.site.set_ssl.get_certificate_list +
										'...</span></td></tr></tbody>\
																				</table>\
																		</div>\
																</div><ul class="help-info-text c7">\
																		<li style="color:red;">' +
										lan.site.set_ssl.bus_tip1 +
										'</li>\
																		<li>' +
										lan.site.set_ssl.bus_tip2 +
										'</li>\
																		<li>' +
										lan.site.set_ssl.bus_tip3 +
										'</li>\
																		<li>' +
										lan.site.set_ssl.bus_tip4 +
										'</li>\
																</ul>'
								);
								$('.service_buy_before').click(function () {
									bt.onlineService();
								});
								bt.fixed_table('ssl_order_list');
								/**
								 * @description 证书购买人工服务
								 * @param {Object} param 支付回调参数
								 * @returns void
								 */
								function open_service_buy(param) {
									var order_info = {},
										is_check = true;
									pay_ssl_layer = bt.open({
										type: 1,
										title: '购买人工服务',
										area: ['790px', '770px'],
										skin: 'service_buy_view',
										content:
											'<div class="bt_business_ssl">\
												<div class="bt_business_tab ssl_applay_info active">\
														<div class="guide_nav"><span class="active">微信支付</span><span >支付宝支付</span></div>\
														<div class="paymethod">\
																<div class="pay-wx" id="PayQcode"></div>\
														</div>\
														<div class="lib-price-box text-center">\
																<span class="lib-price-name f14"><b>总计</b></span>\
																<span class="price-txt"><b class="sale-price"></b>元</span>\
														</div>\
														<div class="lib-price-detailed">\
																<div class="info">\
																		<span class="text-left">商品名称</span>\
																		<span class="text-right"></span>\
																</div>\
																<div class="info">\
																		<span class="text-left">下单时间</span>\
																		<span class="text-right"></span>\
																</div>\
														</div>\
														<div class="lib-prompt"><span>微信扫一扫支付</span></div>\
												</div>\
												<div class="bt_business_tab order_service_check">\
														<div class="prder_pay_service_left">\
																<div class="order_pay_title">支付成功</div>\
																<div class="lib-price-detailed">\
																		<div class="info">\
																				<span class="text-left">商品名称：</span>\
																				<span class="text-right"></span>\
																		</div>\
																		<div class="info-line"></div>\
																		<div class="info">\
																				<span class="text-left">商品价格：</span>\
																				<span class="text-right"></span>\
																		</div>\
																		<div class="info" style="display:block">\
																				<span class="text-left">下单时间：</span>\
																				<span class="text-right"></span>\
																		</div>\
																</div>\
														</div>\
														<div class="prder_pay_service_right">\
																<div class="order_service_qcode">\
																		<div class="order_open_title">请打开微信扫一扫联系人工客服</div>\
																		<div class="order_wx_qcode"><img id="contact_qcode" src="/static/images/customer-qrcode.png" alt="qrcode" style="width: 120px;"><i class="wechatEnterprise"></i></div>\
																</div>\
														</div>\
												</div>\
										</div>',
										success: function (layero, indexs) {
											var order_wxoid = null,
												qq_info = null;

											$('.guide_nav span').click(function () {
												$(this).addClass('active').siblings().removeClass('active');
												$('.lib-prompt span').html($(this).index() == 0 ? '微信扫一扫支付' : '支付宝扫一扫支付');
												$('#PayQcode').empty();
												$('#PayQcode').qrcode({
													render: 'canvas',
													width: 200,
													height: 200,
													text: $(this).index() != 0 ? order_info.alicode : order_info.wxcode,
												});
											});
											reader_applay_qcode(
												$.extend(
													{
														name: '证书安装服务',
														price: param.price,
														time: bt.format_data(new Date().getTime()),
													},
													param
												),
												function (info) {
													check_applay_status(function (rdata) {
														$('.order_service_check').addClass('active').siblings().removeClass('active');
														$('.order_service_check .lib-price-detailed .text-right:eq(0)').html(info.name);
														$('.order_service_check .lib-price-detailed .text-right:eq(1)').html('￥' + info.price);
														$('.order_service_check .lib-price-detailed .text-right:eq(2)').html(info.time);
														$('#ssl_tabs .on').click();
														//人工客服二维码
														$('#contact_qcode').qrcode({
															render: 'canvas',
															width: 120,
															height: 120,
															text: 'https://work.weixin.qq.com/kfid/kfc9151a04b864d993f',
														});
														//缩小展示窗口
														$('.service_buy_view')
															.width(690)
															.height(350)
															.css({
																//设置最外层弹窗大小
																left: (document.body.clientWidth - 690) / 2 + 'px',
																top: (document.body.clientHeight - 350) / 2 + 'px',
															});
													}); //检测支付状态
												}
											); //渲染二维码

											function reader_applay_qcode(data, callback) {
												order_wxoid = data.wxoid;
												qq_info = data.qq;
												order_info = data;

												$('#PayQcode').empty().qrcode({
													render: 'canvas',
													width: 240,
													height: 240,
													text: data.wxcode,
												});
												$('.price-txt .sale-price').html(data.price);
												$('.lib-price-detailed .info:eq(0) span:eq(1)').html(data.name);
												$('.lib-price-detailed .info:eq(1) span:eq(1)').html(data.time);
												if (typeof data.qq != 'undefined') {
													$('.order_pay_btn a:eq(0)').attr({
														href: data.qq,
														target: '_blank',
													});
												} else {
													$('.order_pay_btn a:eq(0)').remove();
												}
												if (callback) callback(data);
											}

											function check_applay_status(callback) {
												bt.send(
													'get_wx_order_status',
													'auth/get_wx_order_status',
													{
														wxoid: order_wxoid,
													},
													function (res) {
														if (res.status) {
															is_check = false;
															if (callback) callback(res);
														} else {
															if (!is_check) return false;
															setTimeout(function () {
																check_applay_status(callback);
															}, 2000);
														}
													}
												);
											}
										},
										cancel: function (index) {
											if (is_check) {
												if (confirm('当前正在支付订单，是否取消？')) {
													layer.close(index);
													is_check = false;
												}
												return false;
											}
										},
									});
								}
								/**
								 * @description 对指定表单元素的内容进行效验
								 * @param {Object} el jqdom对象
								 * @param {String} name 表单元素name名称
								 * @param {*} value 表单元素的值
								 * @returns 返回当前元素的值
								 */
								function check_ssl_user_info(el, name, value, config) {
									el.css('borderColor', '#ccc');
									var status;
									switch (name) {
										case 'domains':
											el = site.domain_dns_type == 'multi' ? $('.dns_domains_multi_view') : el;
											value = bt.strim(value).replace(/\n*$/, '');
											var list = value.split('\n');
											if (value == '') {
												set_info_tips(el, { msg: 'The domain name cannot be empty!', color: 'red' });
												status = false;
											}
											if (!Array.isArray(list)) list = [list];
											$.each(list, function (index, item) {
												if (bt.check_domain(item)) {
													var type = item.indexOf(),
														index = null;
													if (config.code.indexOf('multi') > -1) index = 0;
													if (config.code.indexOf('wildcard') > -1) index = 1;
													if (config.code.indexOf('wildcard') > -1 && config.code.indexOf('multi') > -1) index = 2;
													switch (index) {
														case 0:
															if (list.length > config.limit) {
																set_info_tips(el, { msg: lan.site.set_ssl.more_cert_tip1(config.limit), color: 'red' });
																status = false;
															} else if (list.length == 1) {
																set_info_tips(el, { msg: lan.site.set_ssl.more_cert_tip2(config.limit), color: 'red' });
																status = false;
															}
															break;
														case 1:
															if (item.indexOf('*') != 0) {
																set_info_tips(el, { msg: "Wildcard domain name format error, correct writing '*.bt.cn'", color: 'red' });
																status = false;
															}
															break;
														case 2:
															if (list.length > config.limit) {
																set_info_tips(el, { msg: lan.site.set_ssl.more_cert_tip1(config.limit), color: 'red' });
																status = false;
															} else if (list.length == 1) {
																set_info_tips(el, { msg: lan.site.set_ssl.more_cert_tip2(config.limit), color: 'red' });
																status = false;
															}
															if (item.indexOf('*') != 0) {
																set_info_tips(el, { msg: "Wildcard domain name format error, correct writing '*.bt.cn'", color: 'red' });
																status = false;
															}
															break;
													}
												} else {
													if (value != '') {
														set_info_tips(el, { msg: '【 ' + item + ' 】' + ',Domain name format error!', color: 'red' });
													} else {
														set_info_tips(el, { msg: 'The domain name cannot be empty!', color: 'red' });
													}
													status = false;
												}
											});
											value = list;
											break;
										case 'state':
											if (value == '') {
												set_info_tips(el, { msg: 'The province cannot be empty!', color: 'red' });
												status = false;
											}
											break;
										case 'city':
											if (value == '') {
												set_info_tips(el, { msg: 'Your city/county cannot be empty!', color: 'red' });
												status = false;
											}
											break;
										case 'city':
											if (value == '') {
												set_info_tips(el, { msg: 'Your city/county cannot be empty!', color: 'red' });
												status = false;
											}
											break;
										case 'organation':
											if (value == '') {
												set_info_tips(el, { msg: 'The company name cannot be empty, if it is an individual application, please enter your name!', color: 'red' });
												status = false;
											}
											break;
										case 'address':
											if (value == '') {
												set_info_tips(el, { msg: 'Please enter the company address, cannot be empty, specific requirements see the description', color: 'red' });
												status = false;
											}
											break;
										case 'name':
											if (value == '') {
												set_info_tips(el, { msg: 'User name cannot be empty!', color: 'red' });
												status = false;
											}
											break;
										case 'email':
											if (value == '') {
												set_info_tips(el, { msg: 'User email address cannot be empty!', color: 'red' });
												status = false;
											}
											if (!bt.check_email(value)) {
												set_info_tips(el, { msg: 'User email address format error!', color: 'red' });
												status = false;
											}
											break;
										// case 'mobile':
										// 	if (value != '') {
										// 		if (!bt.check_phone(value)) {
										// 			set_info_tips(el, { msg: 'User mobile phone number format error!', color: 'red' });
										// 			status = false;
										// 		}
										// 	}
										// 	break;
										// case 'phonePre':
										// 	if (value != '') {
										// 		var reg = /^\+\d+/
										// 		if (!reg.test(value)) {
										// 			set_info_tips(el, { msg: 'User mobile phone number format error!', color: 'red' });
										// 			status = false;
										// 		}
										// 	}
										// 	break;
										default:
											status = value;
											break;
									}
									if (typeof status == 'boolean' && status === false) return false;
									status = value;
									return status;
								}

								/**
								 * @description 设置元素的提示和边框颜色
								 * @param {Object} el jqdom对象
								 * @param {Object} config  = {
								 *  @param {String} config.msg 提示内容
								 *  @param {String} config.color 提示颜色
								 * }
								 */
								function set_info_tips(el, config) {
									$('html').append($('<span id="width_test">' + config.msg + '</span>'));
									layer.tips(config.msg, el, { tips: [1, config.color], time: 3000 });
									el.css('borderColor', config.color);
									$('#width_test').remove();
								}
								/**
								 * @description 更换域名验证方式
								 * @param {Number} oid 域名订单ID
								 * @returns void
								 */
								function again_verify_veiw(oid, is_success) {
									var loads = bt.load('Please wait while obtaining verification method...');
									bt.send('get_verify_result', 'ssl/get_verify_result', { uc_id: oid }, function (res) {
										loads.close();
										var type = res.data.dcvList[0].dcvMethod;
										loadT = bt.open({
											type: 1,
											title: lan.site.set_ssl.ver_file(type),
											area: '520px',
											btn: [lan.public.edit, lan.public.cancel],
											content:
												'<div class="bt-form pd15"><div class="line"><span class="tname">Verification mode</span><div class="info-r"><select class="bt-input-text mr5" name="file_rule" style="width:250px"></select></div></div>\
																											<ul class="help-info-text c7">' +
												lan.site.set_ssl.file_ver_tip +
												'</ul>\
																									</div>',
											success: function (layero, index) {
												var _option_list = { 'File Validation (HTTP)': 'HTTP_CSR_HASH', 'File Validation (HTTPS)': 'HTTPS_CSR_HASH', 'DNS Authentication (CNAME resolution)': 'CNAME_CSR_HASH' },
													_option = '';
												$.each(_option_list, function (index, item) {
													_option += '<option value="' + item + '" ' + (type == item ? 'selected' : '') + '>' + index + '</option>';
												});
												$('select[name=file_rule]').html(_option);
											},
											yes: function (index, layero) {
												var new_type = $('select[name=file_rule]').val();
												if (type == new_type) return layer.msg('Duplicate authentication mode', { icon: 2 });
												var loads = bt.load('Changing the verification mode, please wait...');
												bt.send('again_verify', 'ssl/again_verify', { uc_id: oid, dcv_method: new_type }, function (res) {
													loads.close();
													if (res.success) layer.close(index);
													layer.msg(res.res, { icon: res.success ? 1 : 2 });
												});
											},
										});
									});
								}
								/**
								 * @description 验证域名
								 * @param {Number} oid 域名订单ID
								 * @param {Boolean} openTips 是否展示状态
								 * @returns void
								 */
								function verify_order_veiw(oid, is_success, openTips) {
									var loads = bt.load('Obtaining verification results, please wait...');
									bt.send('get_verify_result', 'ssl/get_verify_result', { uc_id: oid }, function (res) {
										loads.close();
										if (!res.status) {
											bt.msg(res);
											return false;
										}
										if (res.status == 'COMPLETE') {
											site.ssl.reload();
											return false;
										}
										var rdata = res.data;
										var domains = [],
											type = rdata.dcvList[0].dcvMethod != 'CNAME_CSR_HASH',
											info = {};
										$.each(rdata.dcvList, function (key, item) {
											domains.push(item['domainName']);
										});
										if (type) {
											info = { fileName: rdata.DCVfileName, fileContent: rdata.DCVfileContent, filePath: '/.well-known/pki-validation/', paths: res.paths, kfqq: res.kfqq };
										} else {
											info = { dnsHost: rdata.DCVdnsHost, dnsType: rdata.DCVdnsType, dnsValue: rdata.DCVdnsValue, paths: res.paths, kfqq: res.kfqq };
										}
										if (is_success) {
											is_success({ type: type, domains: domains, info: info });
											return false;
										}
										loadT = bt.open({
											type: 1,
											title: lan.site.set_ssl.ver_file(type),
											area: '620px',
											content: reader_domains_cname_check({ type: type, domains: domains, info: info }),
											success: function (layero, index) {
												//展示验证状态
												setTimeout(function () {
													if (openTips && res.status == 'PENDING') layer.msg('Verification, please wait patiently', { time: 0, shadeClose: true, icon: 0, shade: 0.3 });
												}, 500);
												var clipboard = new ClipboardJS('.parsing_info .parsing_icon');
												clipboard.on('success', function (e) {
													bt.msg({ status: true, msg: 'Successful copy' });
													e.clearSelection();
												});
												clipboard.on('error', function (e) {
													bt.msg({ status: true, msg: 'Copy failed, please manually ctrl+c copy!' });
												});
												$('.verify_ssl_domain').click(function () {
													verify_order_veiw(oid, false, true);
													layer.close(index);
												});

												$('.set_verify_type').click(function () {
													again_verify_veiw(oid);
													layer.close(index);
												});

												$('.return_ssl_list').click(function () {
													layer.close(index);
													$('#ssl_tabs span.on').click();
												});

												// 重新验证按钮
												$('.domains_table').on('click', '.check_url_results', function () {
													var _url = $(this).data('url'),
														_con = $(this).data('content');
													check_url_txt(_url, _con, this);
												});
											},
										});
									});
								}

								/**
								 * @description 重新验证
								 * @param {String} url 验证地址
								 * @param {String} content 验证内容
								 * @returns 返回验证状态
								 */
								function check_url_txt(url, content, _this) {
									var loads = bt.load('Obtaining verification results, please wait...');
									bt.send('check_url_txt', 'ssl/check_url_txt', { url: url, content: content }, function (res) {
										loads.close();
										var html =
											'<span style="color:red">fail[' +
											res +
											']</span><a href="https://www.aapanel.com/forum/d/19277-business-ssl-certificate-tutorial" target="_blank" class="bt-ico-ask" style="cursor: pointer;">?</a>';
										if (res === 1) {
											html = '<a class="btlink">pass</a>';
										}
										$(_this).parents('tr').find('td:nth-child(2)').html(html);
									});
								}
								/**
								 * @description 渲染验证模板接口
								 * @param {Object} data 验证数据
								 * @returns void
								 */
								function reader_domains_cname_check(data) {
									var html = '';
									if (data.type) {
										var check_html =
											'<div class="bt-table domains_table" style="margin-bottom:20px"><div class="divtable"><table class="table table-hover" style="table-layout:fixed;"><thead><tr><th width="250">URL</th><th width="85">' +
											lan.site.set_ssl.verification_result +
											'</th><th style="text-align:right;">' +
											lan.public.action +
											'</th></thead>';
										var paths = data.info.paths;
										for (var i = 0; i < paths.length; i++) {
											check_html +=
												'<tr><td><span title="' +
												paths[i].url +
												'" class="lib-ssl-overflow-span-style" style="display: inline-block;width: 100%;overflow: hidden;text-overflow: ellipsis;">' +
												paths[i].url +
												'</span></td><td>' +
												(paths[i].status == 1
													? '<a class="btlink">pass</a>'
													: '<span style="color:red">fail[' +
													  paths[i].status +
													  ']</span><a href="https://www.aapanel.com/forum/d/19277-business-ssl-certificate-tutorial" target="_blank" class="bt-ico-ask" style="cursor: pointer;">?</a>') +
												'</td><td style="text-align:right;"><a href="javascript:bt.pub.copy_pass(\'' +
												paths[i].url +
												'\');" class="btlink">copy</a> | <a href="' +
												paths[i].url +
												'" target="_blank" class="btlink">open</a> | <a data-url="' +
												paths[i].url +
												'" data-content="' +
												data.info.fileContent +
												'" class="btlink check_url_results">reverify</a></td>';
										}
										check_html += '</table></div></div>';
										html =
											'<div class="lib-ssl-parsing">\
											<div class="parsing_tips">Please give the following domain name【 <span class="highlight">' +
											data.domains.join('、') +
											'</span> 】Add a verification file. The verification information is as follows：</div>\
											<div class="parsing_parem"><div class="parsing_title">File location：</div><div class="parsing_info"><input type="text" name="filePath"  class="parsing_input border" value="' +
											data.info.filePath +
											'" readonly="readonly" style="width:345px;"/></div></div>\
											<div class="parsing_parem"><div class="parsing_title">File name：</div><div class="parsing_info"><input type="text" name="fileName" class="parsing_input" value="' +
											data.info.fileName +
											'" readonly="readonly" style="width:345px;"/><span class="parsing_icon" data-clipboard-text="' +
											data.info.fileName +
											'">copy</span></div></div>\
											<div class="parsing_parem"><div class="parsing_title" style="vertical-align: top;">File content：</div><div class="parsing_info"><textarea name="fileValue"  class="parsing_textarea" readonly="readonly" style="width:350px;">' +
											data.info.fileContent +
											'</textarea><span class="parsing_icon" style="display: block;width: 60px;border-radius: 3px;" data-clipboard-text="' +
											data.info.fileContent +
											'">copy</span></div></div>' +
											check_html +
											'<div class="parsing_tips" style="font-size:13px;line-height: 24px;">· The verification result is verified by [this server], and the actual verification will be verified by [CA server]. Please wait patiently</br>· Please ensure that all items in the above list are successfully verified and click [Verify domain name] to submit verification again</br>· If the authentication fails for a long time, please change it to [DNS authentication] through [Modify Authentication method].</br>· SSL Adds the file authentication mode ->> <a href="https://www.aapanel.com/forum/d/19277-business-ssl-certificate-tutorial" target="_blank" class="btlink" >View the tutorial</a></div>\
															<div class="parsing_parem" style="padding: 0 0px;"><button type="submit" class="btn btn-success verify_ssl_domain">Verify Domain</button><button type="submit" class="btn btn-default set_verify_type">Modify Auth Mode</button><button type="submit" class="btn btn-default return_ssl_list">Return list</button></div>\
													</div>';
									} else {
										html =
											'<div class="lib-ssl-parsing">\
													<div class="parsing_tips">Please give the following domain name【 <span class="highlight">' +
											data.domains.join('、') +
											'</span> 】add“' +
											data.info.dnsType +
											'”the parsing parameters as follows：</div>\
													<div class="parsing_parem"><div class="parsing_title">Host record：</div><div class="parsing_info"><input type="text" name="host" class="parsing_input" value="' +
											data.info.dnsHost +
											'" readonly="readonly" /><span class="parsing_icon" data-clipboard-text="' +
											data.info.dnsHost +
											'">copy</span></div></div>\
													<div class="parsing_parem"><div class="parsing_title">Record type：</div><div class="parsing_info"><input type="text" name="host" class="parsing_input" value="' +
											data.info.dnsType +
											'" readonly="readonly" style="border-right: 1px solid #ccc;border-radius: 3px;width: 390px;" /></div></div>\
													<div class="parsing_parem"><div class="parsing_title">Record value：</div><div class="parsing_info"><input type="text" name="domains"  class="parsing_input" value="' +
											data.info.dnsValue +
											'" readonly="readonly" /><span class="parsing_icon" data-clipboard-text="' +
											data.info.dnsValue +
											'">copy</span></div></div>\
													<div class="parsing_tips" style="font-size:13px;line-height: 24px;">· The verification result is verified by [this server], and the actual verification will be verified by [CA server]. Please wait patiently</br>· Please ensure that all items in the above list are successfully verified and click [Verify domain name] to submit verification again</br>· If the authentication fails for a long time, please change it to [DNS authentication] through [Modify Authentication method].</br>· How to add domain name resolution，And consult the server operator</br>· <a class="btlink" href="https://www.aapanel.com/forum/d/19277-business-ssl-certificate-tutorial" target="_blank">How do I verify commercial certificates?</a></div>\
													<div class="parsing_parem" style="padding: 0 0px;"><button type="submit" class="btn btn-success verify_ssl_domain">Verify Domain</button><button type="submit" class="btn btn-default set_verify_type">Modify Auth Mode</button><button type="submit" class="btn btn-default return_ssl_list">Return list</button></div>\
											</div>';
									}
									return html;
								}
								// 购买证书信息
								function pay_ssl_business() {
									var order_info = {},
										user_info = {},
										is_check = false;
									var loadT = bt.load(lan.site.set_ssl.get_apply_cert);
									bt.send('get_product_list_v2', 'ssl/get_product_list_v2', {}, function (rdata) {
										loadT.close();
										var res = rdata.res;
										var dataLength = res['data'] && res.data.length,
											data_list = res.data,
											list = [],
											prompt_msg = res.info;
										bt.open({
											type: 1,
											title: lan.site.set_ssl.buy_cert,
											area: ['810px', '832px'],
											skin: 'layer-business-ssl',
											content:
												'\
												<div style="height: 695px; overflow: auto; padding-top: 20px;">\
													<div style="display: flex; align-items: center; justify-content: center; width: 700px; margin: 0 auto; padding: 10px 16px; background: #F2DEDF;color: #A5374A;font-size: 12px;border-radius: 2px;">\
														<span class="glyphicon glyphicon-alert" style="color: #A5374A;"></span>\
														<span style="width: 626px; margin-left: 16px;">' +
												lan.site.set_ssl.bus_cert_tip +
												'</span>\
													</div>\
													<div>\
														<div class="business_ssl_form bt_business_tab active">\
															<div class="bt-form" style="padding: 8px 20px 8px;">\
																<div class="line">\
																	<span class="tname">' +
												lan.site.set_ssl.domain_num +
												'</span>\
																	<div class="info-r">\
																		<div class="domain_number_group">\
																			<div class="domain_number_reduce is_disable" data-type="reduce"></div>\
																			<input type="number" class="domain_number_input" value="" />\
																			<div class="domain_number_add"  data-type="add"></div>\
																		</div>\
																		<div class="unit mt5 domain_number_tips"></div>\
																		<div class="tips_gray mt5"><p>' +
												lan.site.set_ssl.select_domain_num +
												'</p></div>\
																	</div>\
																</div>\
																<div class="line">\
																	<span class="tname">' +
												lan.site.set_ssl.cert_class +
												'</span>\
																	<div class="info-r">\
																		<div class="inlineBlock" style="display:flex">\
																			<div class="ssl_item ssl_type_item mr10" data-type="OV">\
																				<div class="ssl_item_title">' +
												lan.site.set_ssl.ov_cert +
												'</div>\
																				<div class="ssl_item_ps">' +
												lan.site.set_ssl.recom_enterprise +
												'</div>\
																			</div>\
																			<div class="ssl_item ssl_type_item mr10" data-type="DV">\
																				<em>Hot</em>\
																				<div class="ssl_item_title">' +
												lan.site.set_ssl.dv_cert +
												'</div>\
																				<div class="ssl_item_ps">' +
												lan.site.set_ssl.recom_pseson +
												'</div>\
																			</div>\
																			<div class="ssl_item ssl_type_item mr10" data-type="EV">\
																				<div class="ssl_item_title">' +
												lan.site.set_ssl.ev_cert +
												'</div>\
																				<div class="ssl_item_ps">' +
												lan.site.set_ssl.recom_large +
												'</div>\
																			</div>\
																		</div>\
																		<div class="tips_gray ssl_type_tips"></div>\
																	</div>\
																</div>\
																<div class="line">\
																	<span class="tname">' +
												lan.site.set_ssl.cert_brand +
												'</span>\
																	<div class="info-r">\
																		<div class="inlineBlock business_brand_list">\
																			<div class="ssl_item ssl_brand_item mr10" data-type="Positive" title="Positive">Positive</div>\
																			<div class="ssl_item ssl_brand_item mr10" data-type="sslTrus" title="sslTrus">sslTrus</div>\
																			<div class="ssl_item ssl_brand_item mr10" data-type="CFCA" title="CFCA">CFCA</div>\
																			<div class="ssl_item ssl_brand_item mr10" data-type="Digicert" title="Digicert">Digicert</div>\
																			<div class="ssl_item ssl_brand_item mr10" data-type="GeoTrust" title="GeoTrust">GeoTrust</div>\
																			<div class="ssl_item ssl_brand_item mr10" data-type="Sectigo" title="Sectigo">Sectigo</div>\
																		</div>\
																		<div class="tips_gray ssl_brand_tips"></div>\
																	</div>\
																</div>\
																<div class="line">\
																	<span class="tname">' +
												lan.site.set_ssl.cert_type +
												'</span>\
																	<div class="info-r">\
																		<div class="inlineBlock business_price_list">\
																			<div class="ssl_item ssl_price_item mr10">' +
												lan.site.set_ssl.one_domain +
												'</div>\
																			<div class="ssl_item ssl_price_item mr10">' +
												lan.site.set_ssl.more_domain +
												'</div>\
																		</div>\
																		<div class="tips_gray ssl_price_tips"></div>\
																	</div>\
																</div>\
																<div class="line">\
																	<span class="tname">' +
												lan.site.set_ssl.pur_period +
												'</span>\
																	<div class="info-r">\
																		<div class="inlineBlock business_year_list">\
																			<div class="ssl_item ssl_year_item mr10" data-year="1">' +
												lan.site.set_ssl.num_year_test(1) +
												'</div>\
																			<div class="ssl_item ssl_year_item mr10" data-year="2">' +
												lan.site.set_ssl.num_year_test(2) +
												'</div>\
																			<div class="ssl_item ssl_year_item mr10" data-year="3">' +
												lan.site.set_ssl.num_year_test(3) +
												'</div>\
																			<div class="ssl_item ssl_year_item mr10" data-year="4">' +
												lan.site.set_ssl.num_year_test(4) +
												'</div>\
																			<div class="ssl_item ssl_year_item mr10" data-year="5">' +
												lan.site.set_ssl.num_year_test(5) +
												'</div>\
																		</div>\
																		<div class="tips_gray mt5 ssl_year_tips"></div>\
																	</div>\
																</div>\
																<div class="line">\
																	<span class="tname">' +
												lan.site.set_ssl.deploy_service +
												'</span>\
																	<div class="info-r">\
																		<div class="inlineBlock">\
																			<div class="ssl_item ssl_service_item mr10" data-install="0" style="width: auto; padding: 0 20px;">' +
												lan.site.set_ssl.no_necess +
												'</div>\
																				<div class="ssl_item ssl_service_item mr10 active" data-serviceprice="28.9" data-install="1" style="width: auto; padding: 0 20px;">' +
												lan.site.set_ssl.deploy_service +
												'</div>\
																				<span class="unit ssl_service_unit"></span>\
																		</div>\
																		<div class="tips_gray mt5 ssl_service_tips"></div>\
																	</div>\
																</div>\
															</div>\
															<div class="business_ssl_btn">\
																<div class="mr5">\
																	<div class="bname">' +
												lan.site.set_ssl.goods_include +
												':<span class="ml10"></span></div>\
																	<div>' +
												lan.site.set_ssl.total_cost +
												':<div class="present_price ml10">\
																			<span>$278.66</span>/1year（' +
												lan.site.set_ssl.in_service +
												'）\
																		</div>\
																		<div class="original_price">Original price$342/1year</div>\
																	</div>\
																</div>\
																<div class="inlineBlock ml10">\
																	<button type="button" class="business_ssl_pay">' +
												lan.site.set_ssl.buy_now +
												'</button>\
																</div>\
															</div>\
														</div>\
														<div class="bt_business_tab ssl_applay_info">\
															<div class="guide_nav">\
																<span class="active">' +
												lan.site.set_ssl.wechat_pay +
												'</span>\
																<span>' +
												lan.site.set_ssl.Alipay_pay +
												'</span>\
															</div>\
															<div class="paymethod">\
																<div class="pay-wx" id="PayQcode"></div>\
															</div>\
															<div class="lib-price-box text-center">\
																<span class="lib-price-name f14"><b>' +
												lan.site.set_ssl.total +
												'</b></span>\
																<span class="price-txt">$<b class="sale-price"></b></span>\
															</div>\
															<div class="lib-price-detailed">\
																<div class="info">\
																	<span class="text-left">' +
												lan.site.set_ssl.tar_name +
												'</span>\
																	<span class="text-right"></span>\
																</div>\
																<div class="info">\
																	<span class="text-left">' +
												lan.site.set_ssl.order_time +
												'</span>\
																	<span class="text-right"></span>\
																</div>\
															</div>\
															<div class="lib-prompt">\
																<span>' +
												lan.site.set_ssl.wechat_swipe +
												'</span>\
															</div>\
														</div>\
														<div class="bt_business_tab ssl_order_check" style="padding: 25px 60px 0 60px;">\
															<div class="order_pay_title">' +
												lan.site.set_ssl.pay_sus +
												'</div>\
															<div class="lib-price-detailed">\
																<div class="info">\
																	<span class="text-left">' +
												lan.site.set_ssl.tar_name +
												'</span>\
																	<span class="text-right"></span>\
																</div>\
																<div class="info">\
																	<span class="text-left">' +
												lan.site.set_ssl.com_price +
												'</span>\
																	<span class="text-right"></span>\
																</div>\
																<div class="info">\
																	<span class="text-left">' +
												lan.site.set_ssl.order_time +
												'</span>\
																	<span class="text-right"></span>\
																</div>\
															</div>\
															<div class="order_pay_btn">\
																<a href="javascript:;">人工服务</a>\
																<a href="javascript:;" data-type="info">' +
												lan.site.set_ssl.com_info +
												'</a>\
																<a href="javascript:;" data-type="clear">' +
												lan.site.set_ssl.return_list +
												'</a>\
															</div>\
															<ul class="help-info-text c7" style="padding:15px 0 0 70px;font-size:13px;">\
																<li>' +
												lan.site.set_ssl.buy_cert_tip1 +
												'</li>\
															</ul>\
														</div>\
													</div>\
												</div>',
											// <div class="ssl_item ssl_service_item mr10" data-install="1" style="width: 90px;">'+ lan.site.set_ssl.deploy_service +'</div>\
											// <div class="ssl_item ssl_service_item mr10" data-install="2" style="width: 130px;">'+ lan.site.set_ssl.service_secret +'</div>\
											// <li>如果已购买人工服务，请点击“人工服务”咨询帮助。</li>\
											success: function (layero, indexs) {
												$.getScript('https://js.stripe.com/v3/');

												var numBtn = $('.domain_number_reduce,.domain_number_add'),
													ssl_type_item = $('.ssl_type_item'),
													ssl_brand_item = $('.ssl_brand_item'),
													ssl_service_item = $('.ssl_service_item'),
													ssl_price_item = $('.ssl_price_item'),
													ssl_year_item = $('.ssl_year_item'),
													business_brand_list = $('.business_brand_list'),
													input = $('.domain_number_input'),
													ssl_type_tips = $('.ssl_type_tips'),
													ssl_brand_tips = $('.ssl_brand_tips'),
													ssl_year_tips = $('.ssl_year_tips'),
													ssl_price_tips = $('.ssl_price_tips'),
													ssl_service_unit = $('.ssl_service_unit'),
													ssl_service_tips = $('.ssl_service_tips');
												var dataInfo = [],
													ylist = [],
													is_single = false, //是否存在单域名
													is_worldxml = false, //是否存在泛域名
													year = 1,
													serviceprice = 0,
													install = 0,
													add_domain_number = 0,
													order_id = null,
													qq_info = null;

												$('.ssl-service').click(function () {
													bt.onlineService();
												});

												// 数量加减
												numBtn.click(function () {
													var type = $(this).data('type'),
														reduce = input.prev(),
														add = input.next(),
														min = 1,
														max = 99,
														input_val = parseInt(input.val());
													if ($(this).hasClass('is_disable')) {
														layer.msg(type === 'reduce' ? 'The number of current domain names cannot be 0' : 'The number of domain names cannot be greater than 99');
														return false;
													}
													switch (type) {
														case 'reduce':
															input_val--;
															if (min > input_val < max) {
																input.val(min);
															}
															break;
														case 'add':
															input_val++;
															if (min > input_val < max) {
																input.val(input_val);
																add.removeClass('is_disable');
															}
															if (input_val == max) $(this).addClass('is_disable');
															break;
													}
													if (input_val == min) {
														reduce.addClass('is_disable');
													} else if (input.val() == max) {
														add.addClass('is_disable');
													} else {
														reduce.removeClass('is_disable');
														add.removeClass('is_disable');
													}

													reader_product_info({ current_num: parseInt(input_val) });
												});
												$('.domain_number_input').on('input', function () {
													var _input = $(this),
														input_val = parseInt(_input.val()),
														input_min = 1,
														input_max = 99,
														reduce = _input.prev(),
														add = _input.next();
													if (input_val <= input_min) {
														_input.val(input_min);
														reduce.addClass('is_disable');
													} else if (input_val >= input_max) {
														input.val(input_max);
														add.addClass('is_disable');
													} else {
														reduce.removeClass('is_disable');
														add.removeClass('is_disable');
													}
													if (_input.val() == '') {
														_input.val(input_min);
														input_val = input_min;
														reduce.addClass('is_disable');
													}
													reader_product_info({ current_num: parseInt(_input.val()) });
												});

												function automatic_msg() {
													layer.msg('The current certificate brand does not support multi-domain certificate, has automatically switched to the supported certificate brand for you!');
												}

												//总计费用信息
												function reader_product_info(config) {
													config.current_num = config.current_num !== '' ? config.current_num : 1;
													add_domain_number = config.current_num;
													input.val(config.current_num !== '' ? config.current_num : 1);
													var p_index = $('.ssl_price_item.active').index(); //证书类型下标
													var year_list = ylist.filter(function (s) {
														return p_index ? s.code.indexOf('wildcard') > -1 : s.code.indexOf('wildcard') === -1;
													});
													var is_flag = year_list.some(function (s) {
														return s.code.indexOf('multi') > -1 || s.brand === 'Digicert';
													});
													if (p_index) {
														ssl_type_item.eq(2).addClass('disabled');
													} else {
														ssl_type_item.eq(2).removeClass('disabled');
													}
													if (input.val() > 1) {
														// disabled
														//证书类型禁用
														var is_type_disabled = ylist
															.filter(function (s) {
																return !p_index ? s.code.indexOf('wildcard') > -1 : s.code.indexOf('wildcard') === -1;
															})
															.some(function (s) {
																return s.code.indexOf('multi') > -1 || s.brand === 'Digicert';
															});
														if (!is_type_disabled) {
															ssl_price_item.eq(p_index ? 0 : 1).addClass('disabled');
														} else {
															ssl_price_item.eq(p_index ? 0 : 1).removeClass('disabled');
														}
														//证书品牌禁用
														for (var i = 0; i < ssl_brand_item.length; i++) {
															if (ssl_brand_item.eq(i).css('display') !== 'none') {
																var brand_data = ssl_brand_item.eq(i).data();
																if (p_index) {
																	if (!brand_data.is_multi_w) ssl_brand_item.eq(i).addClass('disabled');
																	else ssl_brand_item.eq(i).removeClass('disabled');
																} else {
																	if (!brand_data.is_multi) ssl_brand_item.eq(i).addClass('disabled');
																	else ssl_brand_item.eq(i).removeClass('disabled');
																}
															}
														}
													} else {
														ssl_price_item.eq(p_index ? 0 : 1).removeClass('disabled');
														ssl_brand_item.removeClass('disabled');
													}
													if (!is_flag) {
														if (input.val() > 1) {
															for (var i = 0; i < ssl_brand_item.length; i++) {
																if (ssl_brand_item.eq(i).css('display') !== 'none') {
																	var brand_data = ssl_brand_item.eq(i).data();
																	if (p_index) {
																		if (brand_data.is_multi_w) {
																			automatic_msg();
																			return ssl_brand_item.eq(i).click();
																		}
																	} else {
																		if (brand_data.is_multi) {
																			automatic_msg();
																			return ssl_brand_item.eq(i).click();
																		}
																	}
																}
															}
														}
													}
													//选中的证书信息
													var data_info = year_list.filter(function (s) {
														return $('.domain_number_input').val() > 1 ? (s.brand === 'Digicert' ? s.code.indexOf('multi') === -1 : s.code.indexOf('multi') > -1) : s.code.indexOf('multi') === -1;
													})[0];
													dataInfo = data_info;
													dataInfo['current_num'] = config['current_num'];
													//服务费
													var service_price = [0, data_info.deploy_price / 100 || 0, data_info.install_price_v2 || 0];
													for (var i = 0; i < service_price.length; i++) {
														ssl_service_item.eq(i).data('serviceprice', service_price[i]);
														// if(i == 1){
														// ssl_service_item.eq(i).data('serviceprice', 28.9);
														// }
													}
													serviceprice = $('.ssl_service_item.active').data('serviceprice');
													if ($('.ssl_service_item.active').index()) ssl_service_unit.html('' + lan.site.set_ssl.deploy_cost + '<span class="org">$' + serviceprice + '/1 Time</span>');
													else ssl_service_unit.html('');
													var cur_num = (config.current_num < data_info.num ? data_info.num : config.current_num) - data_info.num;
													var p_price = parseFloat(Number(serviceprice) * 100 + (data_info.price + data_info.add_price * cur_num) * year).toFixed(2);
													if (config.current_num > 1 || data_info.brand === 'Digicert') {
														if (data_info.brand !== 'Digicert') ssl_price_item.eq(0).text('Universal domain');
														if (data_info.brand === 'Digicert') ssl_price_item.eq(0).text('Single domain');
														$('.domain_number_tips').html(lan.site.set_ssl.default_over(data_info.num) + '<span>$' + (data_info.add_price / 100).toFixed(2) + '/one/year</span>');
													} else {
														ssl_price_item.eq(0).text('Single domain');
														$('.domain_number_tips').empty();
													}
													var pp_html = '<span>$' + Number(p_price) / 100 + '</span>/' + year + 'year' + ($('.ssl_service_item.active').index() ? '（' + lan.site.set_ssl.in_service + '）' : ''),
														op_html =
															lan.site.set_ssl.or_price +
															'$' +
															parseFloat(parseFloat((Number(serviceprice) * 100 + (data_info.other_price + data_info.add_price * cur_num) * year) / 100).toFixed(2)) +
															'/' +
															year +
															'year';
													var price_pack = parseFloat(parseFloat(data_info.price * year).toFixed(2)),
														price_extra = data_info.add_price * cur_num * year;
													$('.business_ssl_btn .bname span').html(
														lan.site.set_ssl.default_domain(data_info.num) +
															'$' +
															price_pack / 100 +
															'/' +
															year +
															'year' +
															(cur_num ? lan.site.set_ssl.over_domain(cur_num) + '$' + price_extra / 100 + '/' + year + 'year' : '')
													);
													$('.business_ssl_btn .present_price').html(pp_html);
													$('.business_ssl_btn .original_price').html(op_html);
												}

												setTimeout(function () {
													ssl_type_item.eq(1).click();
												}, 50);
												//证书分类切换
												ssl_type_item.click(function () {
													if ($(this).hasClass('disabled')) return layer.msg(lan.site.set_ssl.dis_tip);
													if (!$(this).hasClass('active')) $(this).addClass('active').siblings().removeClass('active');
													//证书类型
													var type = $(this).data('type'),
														brand_list = []; //品牌类型
													list = dataLength
														? data_list.filter(function (s) {
																return s.type.indexOf(type) > -1;
														  })
														: [];
													var type_tips_list = prompt_msg['type'][type.toLowerCase()],
														type_tips = '';
													for (var i = 0; i < type_tips_list.length; i++) {
														type_tips += '<p class="mt5">' + type_tips_list[i] + '</p>';
													}
													ssl_type_tips.html(type_tips); //提示信息
													$.each(list, function (i, item) {
														brand_list.push(item.brand);
													});
													brand_list = Array.from(new Set(brand_list)); //去重
													var recommend = prompt_msg['recommend'][type.toLowerCase()];
													business_brand_list.find('em').remove();
													business_brand_list.find('[data-type="' + prompt_msg['recommend'][type.toLowerCase()] + '"]').prepend('<em>Hot</em>');
													ssl_brand_item.hide();
													for (var i = 0; i < brand_list.length; i++) {
														business_brand_list.find('[data-type="' + brand_list[i] + '"]').show();
														var b_list = list.filter(function (s) {
															return s.brand === brand_list[i];
														});
														//品牌是否存在多域名
														var is_multi = b_list.some(function (s) {
															return (s.code.indexOf('wildcard') === -1 && s.code.indexOf('multi') > -1) || s.brand === 'Digicert';
														});
														var is_multi_w = b_list.some(function (s) {
															return (s.code.indexOf('wildcard') > -1 && s.code.indexOf('multi') > -1) || s.brand === 'Digicert';
														});
														business_brand_list.find('[data-type="' + brand_list[i] + '"]').data({ is_multi: is_multi, is_multi_w: is_multi_w });
													}
													business_brand_list.find('[data-type="' + recommend + '"]').click();
												});

												//证书品牌
												ssl_brand_item.click(function () {
													var p_index = $('.ssl_price_item.active').index();
													if ($(this).hasClass('disabled')) {
														if (p_index !== -1) {
															for (var i = 0; i < ssl_brand_item.length; i++) {
																if (ssl_brand_item.eq(i).css('display') !== 'none') {
																	var brand_data = ssl_brand_item.eq(i).data();
																	if (p_index) {
																		if (brand_data.is_multi_w) return ssl_brand_item.eq(i).click();
																	} else {
																		if (brand_data.is_multi) return ssl_brand_item.eq(i).click();
																	}
																}
															}
														}
														return layer.msg('The current certificate brand does not support multi-domain wildcard certificates. Please select another brand certificate');
													}
													if (!$(this).hasClass('active')) $(this).addClass('active').siblings().removeClass('active');
													var type = $(this).data('type'),
														years_list = [],
														max_years = 0,
														years_html = '',
														cert_html = '';
													ylist = list.filter(function (s) {
														return s.brand.indexOf(type) > -1;
													});
													brand_type = $('.ssl_type_item.active').data('type');
													var brand_tips_list = prompt_msg['brand'][type === 'Positive' || type === 'sslTrus' ? type : type.toLowerCase()],
														brand_tips = '';
													for (var i = 0; i < brand_tips_list.length; i++) {
														brand_tips += '<p class="mt5">' + brand_tips_list[i] + '</p>';
													}
													ssl_brand_tips.html(brand_tips); //提示信息
													$.each(ylist, function (i, item) {
														years_list.push(item.max_years);
													});
													//是否存在单域名/泛域名按钮
													is_single = ylist.some(function (s) {
														return s.code.indexOf('wildcard') === -1;
													});
													is_worldxml = ylist.some(function (s) {
														return s.code.indexOf('wildcard') > -1;
													});
													if (is_single) {
														ssl_price_item.eq(0).show();
													} else {
														ssl_price_item.eq(0).hide();
													}
													if (is_worldxml) {
														ssl_price_item.eq(1).show();
													} else {
														ssl_price_item.eq(1).hide();
													}
													max_years = Array.from(new Set(years_list))[0];
													for (var i = 0; i < 5; i++) {
														if (i < max_years) {
															ssl_year_item.eq(i).show();
														} else {
															ssl_year_item.eq(i).hide();
														}
													}
													//证书类型点击
													var p_index = $('.ssl_price_item.active').index();
													ssl_price_item.eq(p_index !== -1 ? (!is_worldxml && p_index === 1 ? 0 : p_index) : 0).click();
												});
												//证书类型
												$('.business_ssl_form').on('click', '.ssl_price_item', function () {
													if ($(this).hasClass('disabled')) return layer.msg(lan.site.set_ssl.dis_tip);
													if (!$(this).hasClass('active')) $(this).addClass('active').siblings().removeClass('active');
													var price_tips_list_0 = [lan.site.set_ssl.single_tip1, lan.site.set_ssl.single_tip2],
														price_tips_list_1 = [lan.site.set_ssl.more_tip1, lan.site.set_ssl.more_tip2];
													var price_tips_list = $(this).index() ? price_tips_list_1 : price_tips_list_0,
														price_tips = '';
													for (var i = 0; i < price_tips_list.length; i++) {
														price_tips += '<p class="mt5">' + price_tips_list[i] + '</p>';
													}
													ssl_price_tips.html(price_tips);
													//购买年限点击
													var y_index = $('.ssl_year_item.active').index();

													ssl_year_item.eq(y_index !== -1 && $('.ssl_year_item.active').css('display') !== 'none' ? y_index : 0).click();
												});
												//购买年限
												$('.business_ssl_form').on('click', '.ssl_year_item', function () {
													if (!$(this).hasClass('active')) $(this).addClass('active').siblings().removeClass('active');
													year = $(this).data('year');
													var year_tips_list = prompt_msg['times'][year + '_year'],
														year_tips = '';
													for (var i = 0; i < year_tips_list.length; i++) {
														year_tips += '<p class="mt5">' + year_tips_list[i] + '</p>';
													}
													ssl_year_tips.html(year_tips); //提示信息

													var ser_index = $('.ssl_service_item.active').index();
													ssl_service_item.eq(ser_index !== -1 ? ser_index : 1).click();
												});

												//部署服务点击
												ssl_service_item.click(function () {
													if (!$(this).hasClass('active')) $(this).addClass('active').siblings().removeClass('active');
													var index = $(this).index();
													(serviceprice = $(this).data('serviceprice')), (install = $(this).data('install'));
													ssl_service_tips.html(
														index
															? index === 1
																? 'aaPanel provides manual deployment certificate deployment services from China time 9:00 -18:30 to help customers troubleshoot deployment certificate validity problems and quickly go online'
																: '宝塔提供9:00 - 24:00的人工部署国密算法证书部署服务，帮助客户排查部署证书部署生效问题，快速上线'
															: ''
													);
													var value = $('.domain_number_input').val();
													reader_product_info({ current_num: value === '' ? value : parseInt(value) });
												});

												//购买事件
												$('.business_ssl_pay').click(function () {
													var loadT = bt.load('Payment order is being generated, please wait...'),
														num = 0;
													add_domain_number = input.val();
													if (dataInfo.add_price !== 0) num = parseInt(dataInfo.current_num - dataInfo.num);
													bt.send(
														'apply_cert_order_pay',
														'ssl/apply_cert_order_pay',
														{
															pdata: JSON.stringify({
																pid: dataInfo.pid,
																deploy: install,
																years: year,
																num: num,
															}),
														},
														function (rdata) {
															loadT.close();
															if (rdata.success) {
																is_check = true;
																var res = rdata.res;

																var stripe = Stripe(res.stripe_public_key);
																stripe.redirectToCheckout({ sessionId: res.session_id });
															}
														}
													);
												});
												//支付切换
												$('.guide_nav span').click(function () {
													var price = $('.business_ssl_btn .present_price span').text(),
														is_wx_quota = parseFloat(price) >= 6000;
													if ($(this).index() === 0 && is_wx_quota) {
														layer.msg('Wechat single transaction limit 6000 yuan, please use Alipay payment', {
															icon: 0,
														});
													} else {
														$(this).addClass('active').siblings().removeClass('active');
														$('.lib-prompt span').html($(this).index() == 0 ? lan.site.set_ssl.wechat_swipe : 'Pay with a swipe on Alipay');
														$('#PayQcode').empty();
														$('#PayQcode').qrcode({
															render: 'canvas',
															width: 200,
															height: 200,
															text: $(this).index() != 0 ? order_info.alicode : order_info.wxcode,
														});
													}
												});
												$('.order_pay_btn a').click(function () {
													switch ($(this).data('type')) {
														case 'info':
															confirm_certificate_info(
																$.extend(dataInfo, {
																	oid: order_id,
																	qq: qq_info,
																	install: install ? true : false,
																	limit: add_domain_number,
																})
															);
															break;
														case 'clear':
															layer.close(indexs);
															break;
													}
												});
											},
											cancel: function (index) {
												if (is_check) {
													if (confirm('The order is currently being paid, would you like to cancel it?')) {
														layer.close(index);
														is_check = false;
													}
													return false;
												}
											},
										});
									});
								}
								// 确认证书信息
								function confirm_certificate_info(config) {
									var userLoad = bt.load('Getting user info, please wait...');
									bt.send('get_cert_admin', 'ssl/get_cert_admin', {}, function (rdata) {
										var res = rdata.res;
										userLoad.close();
										var html = '';
										var isWildcard = config.code.indexOf('wildcard') > -1;
										var isMulti = config.code.indexOf('multi') > -1;
										if (typeof pay_ssl_layer != 'undefined') pay_ssl_layer.close();
										if (config.code.indexOf('multi') > -1) {
											if (isWildcard) {
												placeholder = lan.site.set_ssl.more_cert_pl1(config.limit);
											} else {
												placeholder = lan.site.set_ssl.more_cert_pl2(config.limit);
											}
											site.domain_dns_type = 'multi';
											html =
												'<div class="dns_domains_multi_view"><div class="dns_domains_multi_list"></div><div class="dns_domains_add_block"><input type="text" placeholder="Enter the domain name and press Enter to add or select the domain name"/><span class="btlink selct_site_btn" onclick="site.select_site_list(\'dns_hide_domains\',\'' +
												config.code +
												'\')">Select a website domain name</span><textarea id="dns_hide_domains" name="domains"></textarea></div></div><div class="dns_domains_verify"><button class="btn btn-default btn-xs isdnsbtn" onclick="site.check_domain_dns()">Refreshing DNS interface information</button><span class="dns_multi_warring_tips"></span></div>';
										} else {
											if (isWildcard) {
												placeholder = 'single domain wildcard certificate, for example, *.bt.cn';
											} else {
												placeholder = 'single domain name certificate, for example, www.bt.cn';
											}
											site.domain_dns_type = 'one';
											html =
												'<input type="text" disabled="true" readonly="readonly" id="apply_site_name" class="bt-input-text mr5" name="domains" placeholder="' +
												placeholder +
												'" style="margin-right: 60px;"/><div class="damin_dns_result"></div><button class="btn btn-success btn-xs" onclick="site.select_site_list(\'apply_site_name\',\'' +
												config.code +
												'\')" style="">Select domain name</button><button class="btn btn-default btn-xs" onclick="site.select_site_txt(\'apply_site_name\',$(\'#apply_site_name\').val())" style="margin: 5px;">Domain name</button><button class="btn btn-default btn-xs isdnsbtn" onclick="site.check_domain_dns()">Refreshing DNS interface information</button>';
										}
										bt.open({
											type: 1,
											title: lan.site.set_ssl.inpro_cert_info,
											area: '640px',
											content:
												'<div class="bt_form perfect_ssl_info" onsubmit="return false;">\
													<div class="line">\
															<span class="tname">Cert Info</span>\
															<div class="info-r">\
																	<span class="ssl_title">' +
												config.title +
												(config.limit > 1 ? '<span style="margin-left:5px;">，Contains ' + config.limit + 'domain names</span>' : '') +
												'</span>\
															</div>\
													</div>\
													<div class="line">\
															<span class="tname">' +
												lan.site.set_ssl.domain_name +
												'</span>\
															<div class="info-r domain_list_info" style="margin-bottom:-5px;">' +
												html +
												'</div>\
													</div>\
													<div class="line check_model_line">\
															<span class="tname">' +
												lan.site.checking_mode +
												'</span>\
															<div class="info-r flex">\
																<div class="mr20 check_method_item CNAME_CSR_HASH">\
																	<input id="CNAME_CSR_HASH" type="radio" name="dcvMethod" checked="checked" value="CNAME_CSR_HASH">\
																	<label for="CNAME_CSR_HASH">DNS Authentication (CNAME resolution)</label>\
																	<span class="testVerify hide"></span>\
																</div>\
																<div class="mr20 check_method_item HTTP_CSR_HASH"  style="display: ' +
												(isWildcard ? 'none' : 'flex') +
												';">\
																	<input id="HTTP_CSR_HASH" type="radio" name="dcvMethod" value="HTTP_CSR_HASH">\
																	<label for="HTTP_CSR_HASH">File Validation (HTTP)</label>\
																	<span class="testVerify hide"></span>\
																</div>\
																<div class="mr20 check_method_item HTTPS_CSR_HASH" style="display: ' +
												(isWildcard ? 'none' : 'flex') +
												';">\
																	<input id="HTTPS_CSR_HASH" type="radio" name="dcvMethod" value="HTTPS_CSR_HASH">\
																	<label for="HTTPS_CSR_HASH">File Validation (HTTPS)</label>\
																	<span class="testVerify hide"></span>\
																</div>\
															</div>\
													</div>\
													<div style="display: flex; align-items: center;cursor: pointer;line-height: 40px;" class="basics-info">\
									<div class="icon-down-ssl" ><svg width="12.000000" height="12.000000" viewBox="0 0 12 5" fill="none" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">\
									<desc>\
										Created with Pixso.\
									</desc>\
									<defs></defs>\
									<path id="path" d="M0.123291 0.809418L4.71558 5.84385C4.8786 6.02302 5.16846 6.04432 5.33038 5.86389L9.87927 0.783104C10.0412 0.602676 10.04 0.311989 9.87701 0.132816C9.79626 0.0446892 9.68945 0 9.58374 0C9.47693 0 9.36938 0.0459404 9.28827 0.136574L5.02881 4.89284L0.708618 0.15662C0.627869 0.0684967 0.522217 0.0238075 0.415405 0.0238075C0.307434 0.0238075 0.20105 0.0697479 0.119873 0.160381C-0.041626 0.338303 -0.0393677 0.630241 0.123291 0.809418Z" fill-rule="nonzero" fill="#999999"></path>\
										</svg>\
									</div>\
										<span class="basics-title" style="width: 122px">Show user Info</span>\
										<span style="width:100%;border-bottom: 1px solid #EBEEF5;"></span>\
									</div>\
													<div class="line basics-clid">\
															<span class="tname">Local area</span>\
															<div class="info-r">\
															<select class="bt-input-text cou" style="width: 100px;" name="country" placeholder="Country"></select>\
																	<input type="text" class="bt-input-text mr5" name="state" value="' +
												res.state +
												'" placeholder="State/province" style="width: 140px; margin-left: 5px;" data-placeholder="' +
												lan.site.set_ssl.province_pl +
												'">\
																	<input type="text" class="bt-input-text mr5" name="city" value="' +
												res.city +
												'" placeholder="City" style="width: 140px; margin-left: 5px;" data-placeholder="' +
												lan.site.set_ssl.city_pl +
												'" />\
															</div>\
													</div>\
													<div class="line basics-clid" >\
															<span class="tname">' +
												lan.site.set_ssl.address +
												'</span>\
															<div class="info-r">\
																	<input type="text" class="bt-input-text mr5" name="address" value="' +
												res.address +
												'" placeholder="Please enter the detailed address of the company, the specific requirements are described, required fields" />\
															</div>\
													</div>\
													<div class="line basics-clid">\
															<span class="tname">Company name</span>\
															<div class="info-r">\
																	<input type="text" class="bt-input-text mr5" name="organation" value="' +
												res.organation +
												'" placeholder="Company name, For individuals, enter personal name. Mandatory field" />\
															</div>\
													</div>\
													<div class="line basics-clid">\
															<span class="tname">Name</span>\
															<div class="info-r ">\
															<input type="text" class="bt-input-text mr5" style="width: 190px;" name="firstName" value="' +
												res.firstName +
												'" placeholder="firstName" />\
																	<input type="text" class="bt-input-text mr5" style="width: 190px;  margin-left: 15px;" name="name" value="' +
												res.lastName +
												'" placeholder="lastName" />\
															</div>\
													</div>\
													<div class="line basics-clid">\
															<span class="tname">Email</span>\
															<div class="info-r ">\
																	<input type="text" class="bt-input-text mr5" name="email" value="' +
												res.email +
												'" placeholder="Please enter the email address, required field" />\
															</div>\
													</div>\
													<div class="line basics-clid">\
															<span class="tname">' +
												lan.public_backup.mobile_phone_or_email +
												'</span>\
															<div class="info-r">\
															<select class="bt-input-text pre" style="width: 120px; margin-right:5px;" name="phonePre" placeholder="area code"></select>\
																	<input type="text" class="bt-input-text mr5" style="width:270px;" name="mobile" value="' +
												res.mobile +
												'" placeholder="Mobile number. If empty, use current bound number" />\
															</div>\
													</div>\
													<div class="line">\
															<div class="info-r"><button class="btn btn-success submit_ssl_info">' +
												lan.site.set_ssl.sub_info +
												'</button></div>\
													</div>\
													<ul class="help-info-text c7 ssl_help_info">\
														<li style="' +
												(isWildcard ? '' : 'display: none;') +
												'">Wildcard certificates support only DNS authentication</li>\
														<li style="' +
												(isMulti ? '' : 'display: none;') +
												'">Multiple domain names support only DNS authentication</li>\
														<li tyle="color:red">https or http authentication: Ensure that the website can be accessed through http/https</li>\
														<li tyle="color:red">The domain name prefix is www, reminding users to resolve the upper-level root domain name, such as www.bt.cn, please ensure that the resolution of bt.cn</li>\
														<li><a class="btlink" href="https://www.aapanel.com/forum/d/19277-business-ssl-certificate-tutorial" target="_blank">How do I verify commercial certificates?</a></li>\
													</ul>\
													<ul class="help-info-text c7 ssl_help_info" style="display:' +
												(config.code.indexOf('ov') > -1 || config.code.indexOf('ev') > -1 ? 'block' : 'none') +
												'; margin-top: 0;">\
															<li>OV/EV certificate application process conditions：</li>\
															<li>1、Fill in the website authentication information (file authentication or DNS authentication)</li>\
															<li>2、Complete the email authentication, and improve the email content according to the mail sent by CA (just fill in Chinese)</li>\
															<li>3、Enterprise check or love enterprise check, Baidu map, 114best can query relevant enterprise information, and the company name and company address exactly match</li>\
															<li>4、The phone number left by the company or other platforms can guarantee that you can hear the CA certification phone from Monday to Friday (7:00-15:00), the phone number belongs to the United States, please pay attention to answer.</li>\
													</ul>\
											</div>',
											check_dns_interface: function (callback) {
												var val = $('input[name="dcvMethod"]:radio:checked').val();
												if (val !== 'CNAME_CSR_HASH') {
													if (callback) callback();
													return;
												}
												var dns_val = $('.dns_interface_select').val();
												if (dns_val == 'dns') {
													if (callback) callback();
												} else {
													bt.site.get_dns_api(function (res) {
														var config;
														for (var i = 0; i < res.length; i++) {
															if (res[i].name == dns_val) {
																config = res[i];
																break;
															}
														}
														var check = true;
														var title = '';
														if (config && config.data) {
															for (var j = 0; j < config.data.length; j++) {
																if (config.data[j].value === '') {
																	check = false;
																	title = config.title;
																	break;
																}
															}
														}
														if (check) {
															if (callback) callback();
														} else {
															layer.msg('No key is configured for the selected DNS interface [' + title + ']', { icon: 2 });
														}
													});
												}
											},
											success: function (layero, index) {
												$.ajax({
													type: 'GET',
													url: '/static/js/countryCode.json',
													data: 'data',
													dataType: 'JSON',
													success: function (data) {
														countryList = data;
														var _option = '';
														var couOp = '';
														$.each(data, function (index, item) {
															_option += '<option value="+' + item.country_code + '">' + item.country_name_en + '(+' + item.country_code + ')</option>';
															couOp += '<option value="' + item.ab + '">' + item.country_name_en + '</option>';
														});
														var node_pid = $('.pre[name=phonePre]');
														var countrySelect = $('.cou[name=country]');
														node_pid.html(_option);
														node_pid.val(res.tel_prefix);
														countrySelect.html(couOp);
														countrySelect.val(res.country);
													},
												});
												$('.basics-clid').hide();
												if (config.code.indexOf('multi') > -1) {
													$('#CNAME_CSR_HASH').click();
													$('#HTTP_CSR_HASH,#HTTPS_CSR_HASH').attr('disabled', 'disabled');

													// dns_domains_add_block下的input焦点触发时，隐藏selct_site_btn
													$('.dns_domains_add_block input').on('focus blur keyup', function (e) {
														e = e || window.event;
														switch (e.type) {
															case 'focus':
																$('.selct_site_btn').hide();
																break;
															case 'blur':
																$('.selct_site_btn').css('display', 'inline-block');
																break;
															case 'keyup':
																if (e.keyCode != 13 && e.type == 'keyup') return false;
																var val = $(this).val();
																if (!bt.check_domain(val)) return layer.msg('Domain name format error', { icon: 2 });
																site.domain_dns_list.push(val);
																$(this).val(''); // 清空输入框
																site.refresh_dns_interface();
																break;
														}
													});
												}
												$('.perfect_ssl_info').data('code', config.code);
												var _this_layer = this;
												bt_tools.send({ url: '/site?action=GetDnsApi' }, function (data) {
													site.dns_configured_table = site.data_treating(data);
													site.add_dns_interface();
													// 基础信息隐藏显示
													$('.basics-info').click(function () {
														if ($('.basics-info').hasClass('active')) {
															$('.basics-info').removeClass('active');
															$('.basics-title').text('Show user Info');
															$('.basics-clid').hide();
														} else {
															$('.basics-info').addClass('active');
															$('.basics-title').text('Hide user Info');
															$('.basics-clid').show();
															//config.code.含有ov、ev时，隐藏公司详细地址
															// if(config.code.indexOf('ov') == -1 || config.code.indexOf('ev') == -1){
															// 	$('.basics-clid').eq(1).hide();
															// }
														}
														$('.ssl_help_info').toggle();
													});
													// 判断基础信息中是否存在空置，将基础信息自动显示
													$('.basics-clid input').each(function () {
														// isMulti为false时，不需要验证公司详细地址
														if (!isMulti && $(this).attr('name') == 'address') return true;
														if ($(this).val() == '') {
															$('.basics-info').click();
															return false;
														}
													});

													// 验证方式
													$('input[name="dcvMethod"]').change(function () {
														var val = $(this).val();
														if (val == 'CNAME_CSR_HASH') {
															site.add_dns_interface();
														} else {
															site.remove_dns_interface();
														}
													});

													// 公司详细地址联动
													$('.perfect_ssl_info').on('input', 'input[name="state"], input[name="city"]', function (e) {
														var is_ovev = config.code.indexOf('ov') > -1 || config.code.indexOf('ev') > -1;
														if (!is_ovev) {
															var state = $('.perfect_ssl_info input[name="state"]').val();
															var city = $('.perfect_ssl_info input[name="city"]').val();
															$('.perfect_ssl_info input[name="address"]').val(state + city);
														}
													});
													$('.perfect_ssl_info')
														.on('focus', 'input[type=text],textarea', function () {
															var placeholder = $(this).attr('placeholder');
															$('html').append($('<span id="width_test">' + placeholder + '</span>'));
															$(this).attr('data-placeholder', placeholder);
															layer.tips(placeholder, $(this), { tips: [1, '#20a53a'], time: 0 });
															$(this).attr('placeholder', '');
															$('#width_test').remove();
														})
														.on('blur', 'input[type=text],textarea', function () {
															var name = $(this).attr('name'),
																val = $(this).val();
															layer.closeAll('tips');
															$(this).attr('placeholder', $(this).attr('data-placeholder'));
															check_ssl_user_info($(this), name, val, config);
														});
													function btserializeDiv(div) {
														var result = {};
														var elements = div.querySelectorAll('input, select, textarea');
														for (var i = 0; i < elements.length; i++) {
															var element = elements[i];
															var name = element.name;
															var value = element.value;
															if (name && !element.disabled) {
																result[name] = value;
															}
														}
														return result;
													}
													$('.submit_ssl_info').on('click', function () {
														var data = {},
															// form = $('.perfect_ssl_info').serializeObject(),
															form = btserializeDiv(document.querySelector('.perfect_ssl_info')),
															is_ovev = config.code.indexOf('ov') > -1 || config.code.indexOf('ev') > -1,
															loadT = null;
														// var reg = /^[\u4E00-\u9FA5]+$/;
														// if (form.name.length < 2 || !reg.test(form.name)) return layer.msg('The name shall be Chinese and two characters or more in length');
														$('.perfect_ssl_info')
															.find('input,textarea')
															.each(function () {
																var name = $(this).attr('name'),
																	value = $(this).val(),
																	value = check_ssl_user_info($(this), name, value, config);
																if (typeof value === 'boolean') {
																	form = false;
																	return false;
																}
																form[name] = value;
															});
														form.phonePre = $('.perfect_ssl_info [name=phonePre]').val();
														form.phonePre = $('.perfect_ssl_info [name=phonePre]').val();
														if (typeof form == 'boolean') return false;
														delete form['undefined']; // 删除undefined
														form['domains'] = site.domain_dns_list;

														if (!is_ovev) form['address'] = form['state'] + form['city'];
														if (typeof config.limit == 'undefined') config.limit = config.num;
														if (form.domains.length < config.limit) {
															bt.confirm({ title: 'Tips', msg: 'The current certificate supports ' + config.limit + ' domain names. Do you want to continue to add domain names?' }, function () {
																req(true);
															});
															return false;
														}
														req(true);
														function req(verify) {
															if (verify) {
																bt.open({
																	title: 'The user information is confirmed twice',
																	area: ['600px'],
																	btn: ['Continue to submit', 'Cancel'],
																	content:
																		'<div class="bt_form certificate_confirm" style="font-size: 12px;padding-left: 25px">' +
																		'<div class="line basics-clid">' +
																		'<span class="tname">Local area</span>' +
																		'<div class="info-r">' +
																		'<select class="bt-input-text" style="width: 100px;" name="country" placeholder="Country"></select>' +
																		'<input type="text" class="bt-input-text mr5" name="state" value="' +
																		form.state +
																		'" placeholder="State/province" style="width: 140px; margin-left: 5px;" data-placeholder="' +
																		lan.site.set_ssl.province_pl +
																		'">' +
																		'<input type="text" class="bt-input-text mr5" name="city" value="' +
																		form.city +
																		'" placeholder="City" style="width: 140px; margin-left: 5px;" data-placeholder="' +
																		lan.site.set_ssl.city_pl +
																		'" />' +
																		'</div>' +
																		'</div>' +
																		'<div class="line basics-clid">' +
																		'<span class="tname">Address</span>' +
																		'<div class="info-r">' +
																		'<input type="text" class="bt-input-text mr5" name="address" value="' +
																		form.address +
																		'" placeholder="Please enter the detailed address of the company, the specific requirements are described, required fields" />' +
																		'</div>' +
																		'</div>' +
																		'<div class="line basics-clid">' +
																		'<span class="tname">Company name</span>' +
																		'<div class="info-r">' +
																		'<input type="text" class="bt-input-text mr5" name="organation" value="' +
																		form.organation +
																		'" placeholder="Company name, For individuals, enter personal name. Mandatory field" />' +
																		'</div>' +
																		'</div>' +
																		'<div class="line basics-clid">' +
																		'<span class="tname">Name</span>' +
																		'<div class="info-r ">' +
																		'<input type="text" class="bt-input-text mr5" style="width: 190px; " name="firstName" value="' +
																		form.firstName +
																		'" placeholder="firstName" />' +
																		'<input type="text" class="bt-input-text mr5" style="width: 190px; margin-left: 15px;" name="name" value="' +
																		form.name +
																		'" placeholder="lastName" />' +
																		'</div>' +
																		'</div>' +
																		'<div class="line basics-clid">' +
																		'<span class="tname">Email</span>' +
																		'<div class="info-r ">' +
																		'<input type="text" class="bt-input-text mr5" name="email" value="' +
																		form.email +
																		'" placeholder="Please enter the email address, required field" />' +
																		'</div>' +
																		'</div>' +
																		'<div class="line basics-clid">' +
																		'<span class="tname">' +
																		lan.public_backup.mobile_phone_or_email +
																		'</span>' +
																		'<div class="info-r">' +
																		'<select class="bt-input-text" style="width: 120px; margin-right:5px;"  value="' +
																		form.phonePre +
																		'" name="phonePre" placeholder="area code"></select>' +
																		'<input type="text" class="bt-input-text mr5" style="width:275px;" name="mobile" value="' +
																		form.mobile +
																		'" placeholder="Mobile number. If empty, use current bound number" />' +
																		'</div>' +
																		'</div>' +
																		'</ul>' +
																		'</div>',
																	yes: function () {
																		var isVerify = true;
																		$('.certificate_confirm')
																			.find('input')
																			.each(function () {
																				var name = $(this).attr('name'),
																					value = $(this).val(),
																					value = check_ssl_user_info($(this), name, value, config);
																				if (typeof value === 'boolean') {
																					form = false;
																					return false;
																				}
																				form[name] = value;
																			});
																		req(false);
																	},
																	success: function () {
																		if (countryList.length > 0) {
																			var _option = '';
																			var couOp = '';
																			$.each(countryList, function (index, item) {
																				_option += '<option value="+' + item.country_code + '">' + item.country_name_en + '(+' + item.country_code + ')</option>';
																				couOp += '<option value="' + item.ab + '">' + item.country_name_en + '</option>';
																			});
																			var node_pid = $('[name=phonePre]');
																			var countrySelect = $('[name=country]');
																			node_pid.html(_option);
																			node_pid.val(form.phonePre);
																			countrySelect.html(couOp);
																			countrySelect.val(form.country);
																		}
																		// 	$.ajax({
																		// 		type: "GET",
																		// 		url: "/static/js/countryCode.json",
																		// 		data: "data",
																		// 		dataType: "JSON",
																		// 		success: function (data) {
																		// 				console.log(data);

																		// 		}
																		// })
																		$('.certificate_confirm [name="organation"]').change(function () {
																			$('.perfect_ssl_info [name="organation"]').val($(this).val());
																			form.organation = $(this).val();
																		});
																		$('.certificate_confirm [name="address"]').change(function () {
																			$('.perfect_ssl_info [name="address"]').val($(this).val());
																			form.address = $(this).val();
																		});
																		$('.checkInfo').on('click', function (e) {
																			window.open('https://www.qcc.com/web/search?key=' + $('.certificate_confirm [name="organation"]').val());
																		});
																	},
																});
																return false;
															}
															_this_layer.check_dns_interface(function () {
																var loadT = bt.load('Please wait while submitting certificate information...');
																var auth_to = $("[name='dns_select']") ? $("[name='dns_select']").val() : '';
																bt.send(
																	'apply_order_ca',
																	'ssl/apply_order_ca',
																	{
																		pdata: JSON.stringify({
																			pid: config.pid,
																			oid: config.oid,
																			domains: form.domains,
																			dcvMethod: $("[name='dcvMethod']:checked").val(),
																			auth_to: auth_to,
																			uc_id: config.uc_id,
																			Administrator: {
																				job: 'General affairs',
																				postCode: '523000',
																				country: form.country,
																				firstName: form.firstName,
																				lastName: form.name,
																				state: form.state,
																				city: form.city,
																				address: form.address,
																				organation: form.organation,
																				email: form.email,
																				tel_prefix: form.phonePre,
																				mobile: form.mobile,
																				lastName: form.name,
																			},
																		}),
																	},
																	function (res) {
																		loadT.close();
																		if (typeof res.msg == 'object') {
																			for (var key in res.msg.errors) {
																				if (Object.hasOwnProperty.call(res.msg.errors, key)) {
																					var element = res.msg.errors[key];
																					bt.msg({
																						status: false,
																						msg: element,
																					});
																				}
																			}
																		} else {
																			if (res.caa_list) {
																				site.show_domain_error_dialog(res.caa_list, res.msg);
																			} else {
																				bt.msg({ status: res.success, msg: res.res });
																			}
																		}
																		if (res.success) {
																			layer.close(index);
																			verify_order_veiw(config.uc_id);
																			$('#ssl_tabs span.on').click();
																		}
																	}
																);
															});
														}
													});

													$('.check_method_item label').click(function (e) {
														e.stopPropagation();
													});

													$('.check_method_item').click(function () {
														// 选中
														$(this).find('label').trigger('click');
														// 判断是否显示异常
														var show = $(this).data('show-tips');
														if (!show) return;
														$(this).data('show-tips', false);
														// 判断是否存在异常数据
														var data = $(this).data('error-data');
														if (!data) return;
														$(this).find('.error-link').trigger('click');
													});

													$('.check_method_item').on('click', '.error-link', function (e) {
														e.stopPropagation();
														var data = $(this).parents('.check_method_item').data('error-data');

														if ($.isPlainObject(data)) {
															site.show_domain_error_dialog(data);
														}
														if (Array.isArray(data)) {
															var html = '';
															$.each(data, function (i, item) {
																html += '<p>' + item + '</p>';
															});
															layer.msg(html, {
																icon: 2,
																shade: 0.3,
																closeBtn: 2,
																time: 0,
																success: function ($layer) {
																	$layer.css({ 'max-width': '560px' });
																	var width = $(window).width();
																	var lWidth = $layer.width();
																	$layer.css({
																		left: (width - lWidth) / 2 + 'px',
																	});
																},
															});
														}
													});

													var Timer = null;
													$('.CNAME_CSR_HASH,.HTTP_CSR_HASH,.HTTPS_CSR_HASH').hover(
														function () {
															var $this = $(this);
															var data = $(this).data('error-data');
															if (data) return;
															var arry = [
																'If the website has not been filed, optional [DNS verification]',
																'If the 301, 302, forced HTTPS, and reverse proxy functions are not enabled, select HTTP',
																'If the website enables "mandatory HTTPS", please select "HTTPS verification".',
															];
															var tips = arry[$this.index()];
															clearTimeout(Timer);
															Timer = setTimeout(function () {
																$this.data({
																	tips: layer.tips(tips, $this.find('label'), { tips: 1, time: 0 }),
																});
															}, 200);
														},
														function () {
															clearTimeout(Timer);
															layer.close($(this).data('tips'));
														}
													);
												});
											},
										});
									});
								}
								$('.ssl_business_application').click(function () {
									pay_ssl_business();
								});
								//订单证书操作
								$('.ssl_order_list')
									.unbind('click')
									.on('click', '.options_ssl', function () {
										var type = $(this).data('type'),
											tr = $(this).parents('tr');
										itemData = order_list[tr.data('index')];
										switch (type) {
											case 'deploy_ssl': // 部署证书
												bt.confirm(
													{
														title: 'Deployment certificate',
														msg:
															'Whether to deploy the certificate and whether to continue？<br>Certificate type：' +
															itemData.title +
															' <br>Certificate supported domain name：' +
															itemData.domains.join('、') +
															'<br>Deployment site name:' +
															web.name +
															'',
													},
													function (index) {
														var loads = bt.load('Please wait while certificates are deployed...');
														bt.send('set_cert', 'ssl/set_cert', { uc_id: itemData.uc_id, siteName: web.name }, function (rdata) {
															layer.close(index);
															$('#webedit-con').empty();
															site.set_ssl(web);
															site.ssl.reload();
															bt.msg(rdata);
														});
													}
												);
												break;
											case 'verify_order': // 验证订单
												verify_order_veiw(itemData.uc_id);
												break;
											case 'clear_order': // 取消订单
												bt.confirm(
													{
														title: 'Cancel order',
														msg: 'Whether to cancel the order, the order domain name [' + itemData.domains.join('、') + '], whether to continue？',
													},
													function (index) {
														var loads = bt.load('Cancelling order, please wait...');
														bt.send('cancel_cert_order', 'ssl/cancel_cert_order', { oid: itemData.oid }, function (rdata) {
															layer.close(index);
															if (rdata.status) {
																$('#ssl_tabs span:eq(2)').click();
																setTimeout(function () {
																	bt.msg(rdata);
																}, 2000);
															}
															bt.msg(rdata);
														});
													}
												);
												break;
											case 'perfect_user_info': //完善用户信息
												confirm_certificate_info(itemData);
												break;
											case 'renewal_ssl':
												renewal_ssl_view(itemData);
												break;
										}
									});
							} else {
								robj.append('<div class="alert alert-warning" style="padding:10px">' + lan.site.set_ssl.no_bind + '</div>');
								var datas = [
									{ title: lan.public.user, name: 'bt_username', value: rdata.email, width: '260px', placeholder: lan.public_backup.mobile_phone_or_email },
									{ title: lan.public.pass, type: 'password', name: 'bt_password', value: rdata.email, width: '260px' },
									{
										title: ' ',
										items: [
											{
												text: lan.public_backup.login,
												name: 'btn_ssl_login',
												type: 'button',
												callback: function (sdata) {
													bt.pub.login_btname(sdata.bt_username, sdata.bt_password, function (ret) {
														if (ret.status) site.reload(7);
													});
												},
											},
											{
												text: lan.site.set_ssl.register_ac,
												name: 'bt_register',
												type: 'button',
												callback: function (sdata) {
													window.open('https://www.aapanel.com/user_admin/register');
												},
											},
										],
									},
								];
								for (var i = 0; i < datas.length; i++) {
									var _form_data = bt.render_form_line(datas[i]);
									robj.append(_form_data.html);
									bt.render_clicks(_form_data.clicks);
								}
								robj.append(
									bt.render_help([
										lan.site.set_ssl.bind_tip1 + '<a class="btlink" target="_blank" href="https://www.racent.com/sectigo-ssl">' + lan.site.set_ssl.click_view + '</a>',
										lan.site.set_ssl.bind_tip2,
									])
								);
							}
						});
					},
				},
				{
					title: "Let's Encrypt",
					callback: function (robj) {
						robj = $('#webedit-con .tab-con');
						// console.log(robj,'obj');
						acme.get_account_info(function (let_user) {});
						acme.id = web.id;
						if (rdata.status && rdata.type == 1) {
							var cert_info = '';
							if (rdata.cert_data['notBefore']) {
								cert_info =
									'<div style="margin-bottom: 10px;padding: 10px;" class="alert alert-success">\
                                  <span style="display: inline-block;overflow: hidden;min-width: 49%;text-overflow: ellipsis;white-space: nowrap;max-width: 100%;"><b>' +
									lan.site.deploy_success_cret +
									'</b>' +
									lan.site.try_renew_cret +
									'</span>\
                                  <span style="display: inline-block;overflow: hidden;min-width: 49%;text-overflow: ellipsis;white-space: nowrap;max-width: 100%;">\
                                  <b>' +
									lan.site.cert_brand +
									'</b>' +
									rdata.cert_data.issuer +
									'</span>\
                                  <span style="display: inline-block;overflow: hidden;min-width: 49%;text-overflow: ellipsis;white-space: nowrap;max-width: 100%;"><b>' +
									lan.site.auth_domain +
									'</b> ' +
									(rdata.cert_data.dns ? rdata.cert_data.dns.join(', ') : '') +
									'</span>\
                                  <span style="display: inline-block;overflow: hidden;min-width: 49%;text-overflow: ellipsis;white-space: nowrap;max-width: 100%;"><b>' +
									lan.site.expire_time +
									'</b> ' +
									rdata.cert_data.notAfter +
									'</span></div>';
							}
							robj.append('<div>' + cert_info + '<div><span>' + lan.site.ssl_key + '</span><span style="padding-left:190px">' + lan.site.ssl_crt + '</span></div></div>');
							var datas = [
								{
									items: [
										{ name: 'key', width: '48%', height: '220px', type: 'textarea', value: rdata.key },
										{ name: 'csr', width: '48%', height: '220px', type: 'textarea', value: rdata.csr },
									],
								},
								{
									items: [
										{
											text: lan.site.ssl_close,
											name: 'btn_ssl_close',
											hide: !rdata.status,
											type: 'button',
											callback: function (sdata) {
												site.ssl.set_ssl_status('CloseSSLConf', web.name);
											},
										},
										{
											text: lan.site.ssl_renew,
											name: 'btn_ssl_renew',
											hide: !rdata.status,
											type: 'button',
											callback: function (sdata) {
												site.ssl.renew_ssl(web.name, rdata.auth_type, rdata.index);
											},
										},
									],
								},
							];
							for (var i = 0; i < datas.length; i++) {
								var _form_data = bt.render_form_line(datas[i]);
								robj.append(_form_data.html);
								bt.render_clicks(_form_data.clicks);
							}
							robj
								.find('textarea')
								.css({
									'background-color': '#f6f6f6',
									resize: 'none',
								})
								.attr('readonly', true);
							robj.find('[name=csr]').css('margin-right', '0');
							var helps = [lan.site.ssl_tips1, lan.site.ssl_tips2, lan.site.ssl_tips3, lan.site.ssl_tips4, lan.site.ssl_tips5];
							robj.append(bt.render_help([lan.site.ssl_help_2, lan.site.ssl_help_3]));
							return;
						}
						bt.site.get_site_domains(web.id, function (ddata) {
							var helps = [
								[lan.site.bt_ssl_help_5, lan.site.bt_ssl_help_8, lan.site.bt_ssl_help_9, lan.site.ssl_tips5],
								[lan.site.dns_check_tips1, lan.site.dns_check_tips2, lan.site.dns_check_tips3, lan.site.dns_check_tips4],
							];
							var datas = [
								{
									title: lan.site.checking_mode,
									items: [
										{
											name: 'check_file',
											text: lan.site.file_check,
											type: 'radio',
											callback: function (obj) {
												$('.checks_line').remove();
												$(obj).siblings().removeAttr('checked');

												$('.help-info-text').html($(bt.render_help(helps[0])));
												//var _form_data = bt.render_form_line({ title: ' ', class: 'checks_line label-input-group', items: [{ name: 'force', type: 'checkbox', value: true, text: '提前校验域名(提前发现问题,减少失败率)' }] });
												//$(obj).parents('.line').append(_form_data.html);

												$('#ymlist li input[type="checkbox"]').each(function () {
													if ($(this).val().indexOf('*') >= 0) {
														$(this).parents('li').hide();
													}
												});
											},
										},
										{
											name: 'check_dns',
											text: lan.site.check_dns,
											type: 'radio',
											callback: function (obj) {
												$('.checks_line').remove();
												$(obj).siblings().removeAttr('checked');
												$('.help-info-text').html($(bt.render_help(helps[1])));
												$('#ymlist li').show();

												var arrs_list = [],
													arr_obj = {};
												bt.site.get_dns_api(function (api) {
													site.dnsapi = {};

													for (var x = 0; x < api.length; x++) {
														site.dnsapi[api[x].name] = {};
														site.dnsapi[api[x].name].s_key = 'None';
														site.dnsapi[api[x].name].s_token = 'None';
														if (api[x].data) {
															site.dnsapi[api[x].name].s_key = api[x].data[0].value;
															site.dnsapi[api[x].name].s_token = api[x].data[1].value;
														}
														arrs_list.push({ title: api[x].title, value: api[x].name });
														arr_obj[api[x].name] = api[x];
													}

													var data = [
														{
															title: lan.site.choose_dns,
															class: 'checks_line',
															items: [
																{
																	name: 'dns_select',
																	width: 'auto',
																	type: 'select',
																	items: arrs_list,
																	callback: function (obj) {
																		var _val = obj.val();
																		$('.set_dns_config').remove();
																		var _val_obj = arr_obj[_val];
																		var _form = {
																			title: '',
																			area: '530px',
																			list: [],
																			btns: [{ title: lan.site.turn_off, name: 'close' }],
																		};

																		var helps = [];
																		if (_val_obj.data !== false) {
																			_form.title = lan.site.set + '【' + _val_obj.title + '】' + lan.site.interface;
																			if (_val_obj.help == 'How to get API Token') {
																				_val_obj.help =
																					'<a class="btlink"  target="_blank" href="https://www.aapanel.com/forum/d/3375-3375-set-the-clouldflare-apt-token-for-dns-editing-permissions">' +
																					_val_obj.help +
																					'</a>';
																			}
																			helps.push(_val_obj.help);
																			var is_hide = true;
																			for (var i = 0; i < _val_obj.data.length; i++) {
																				_form.list.push({
																					title: _val_obj.data[i].name,
																					name: _val_obj.data[i].key,
																					value: _val_obj.data[i].value,
																				});
																				if (!_val_obj.data[i].value) is_hide = false;
																			}
																			if (_val_obj.title == 'CloudFlare') {
																				_form.list.push({
																					html:
																						'<div class="line"><span class="tname">API-Limit</span><div class="info-r c4"><div class="index-item" style="padding-top:7px"><input class="btswitch btswitch-ios" name="API_Limit" id="API_Limit" type="checkbox" ' +
																						(_val_obj.API_Limit ? 'checked' : null) +
																						'><label class="btswitch-btn" for="API_Limit"></label></div></div></div>',
																				});
																			}
																			_form.btns.push({
																				title: lan.site.save,
																				css: 'btn-success',
																				name: 'btn_submit_save',
																				callback: function (ldata, load) {
																					bt.site.set_dns_api({ pdata: JSON.stringify(ldata) }, function (ret) {
																						if (ret.status) {
																							load.close();
																							robj.find('input[type="radio"]:eq(0)').trigger('click');
																							robj.find('input[type="radio"]:eq(1)').trigger('click');
																						}
																						bt.msg(ret);
																					});
																				},
																			});
																			if (is_hide) {
																				obj.after('<button class="btn btn-default btn-sm mr5 set_dns_config">' + lan.site.set + '</button>');
																				$('.set_dns_config').click(function () {
																					var _bs = bt.render_form(_form);
																					$('div[data-id="form' + _bs + '"]').append(bt.render_help(helps));
																				});
																			} else {
																				var _bs = bt.render_form(_form);
																				$('div[data-id="form' + _bs + '"]').append(bt.render_help(helps));
																			}
																		}
																	},
																},
															],
														},
														{
															title: ' ',
															class: 'checks_line label-input-group',
															items: [
																{
																	css: 'label-input-group ptb10',
																	text: 'Automatically combine pan-domain names',
																	name: 'app_root',
																	type: 'checkbox',
																},
															],
														},
													];
													for (var i = 0; i < data.length; i++) {
														var _form_data = bt.render_form_line(data[i]);
														$(obj).parents('.line').append(_form_data.html);
														bt.render_clicks(_form_data.clicks);
													}
												});
											},
										},
									],
								},
							];

							for (var i = 0; i < datas.length; i++) {
								var _form_data = bt.render_form_line(datas[i]);
								robj.append(_form_data.html);
								bt.render_clicks(_form_data.clicks);
							}
							var _ul = $(
								'<ul id="ymlist" class="domain-ul-list"><div style="line-height: 25px;"><label style="margin-bottom: 0;height: 25px;line-height: 25px;"><input class="checkbox-text" type="checkbox" style="margin: 0 5px 0 0;vertical-align: middle;"><span style="font-weight: 500;cursor: pointer;">Select All</span></label></div></ul>'
							);
							for (var i = 0; i < ddata.domains.length; i++) {
								if (ddata.domains[i].binding === true) continue;
								_ul.append('<li style="cursor: pointer;"><input class="checkbox-text" type="checkbox" value="' + ddata.domains[i].name + '">' + ddata.domains[i].name + '</li>');
							}
							var _line = $("<div class='line mtb10'></div>");
							_line.append('<span class="tname text-center">' + lan.site.domain + '</span>');
							_line.append(_ul);
							robj.append(_line);
							robj.find('input[type="radio"]').parent().addClass('label-input-group ptb10');
							$('#ymlist li input').click(function (e) {
								e.stopPropagation();
								var a = true;
								$('#ymlist li input').each(function () {
									var o = $(this).prop('checked');
									if (!o) {
										a = false;
										return false;
									}
								});
								$('#ymlist div input').prop('checked', a);
							});
							$('#ymlist li').click(function () {
								var o = $(this).find('input'),
									a = true;
								if (o.prop('checked')) {
									o.prop('checked', false);
								} else {
									o.prop('checked', true);
								}
								$('#ymlist li input').each(function () {
									var o = $(this).prop('checked');
									if (!o) {
										a = false;
										return false;
									}
								});
								$('#ymlist div input').prop('checked', a);
							});
							$('#ymlist div').click(function () {
								var o = $('#ymlist div input'),
									p = $('#ymlist input');
								if (o.prop('checked')) {
									p.prop('checked', true);
								} else {
									p.prop('checked', false);
								}
							});
							var _btn_data = bt.render_form_line({
								title: ' ',
								text: lan.site.btapply,
								name: 'letsApply',
								type: 'button',
								callback: function (ldata) {
									ldata['domains'] = [];
									$('#ymlist li:visible input[type="checkbox"]:checked').each(function () {
										ldata['domains'].push($(this).val());
									});
									// console.log(ldata)
									var auth_type = 'http';
									var auth_to = web.id;
									var auto_wildcard = '0';
									if (ldata.check_dns) {
										auth_type = 'dns';
										auth_to = 'dns';
										auto_wildcard = ldata.app_root ? '1' : '0';
										if (ldata.dns_select !== auth_to) {
											if (!site.dnsapi[ldata.dns_select].s_key) {
												layer.msg('No key information is set for the specified dns interface');
												return;
											}
											auth_to = ldata.dns_select + '|' + site.dnsapi[ldata.dns_select].s_key + '|' + site.dnsapi[ldata.dns_select].s_token;
										}
									}
									if (ldata['domains'].length <= 0) {
										return layer.msg('Need at least a domain name!', { icon: 2 });
									}
									site.show_certificate_confirm(web.name, function () {
										acme.apply_cert(ldata['domains'], auth_type, auth_to, auto_wildcard, function (res) {
											site.ssl.ssl_result(res, auth_type, web.name);
										});
									});
								},
							});
							robj.append(_btn_data.html);
							bt.render_clicks(_btn_data.clicks);

							robj.append(bt.render_help(helps[0]));
							robj.find('input[type="radio"]:eq(0)').trigger('click');
						});
					},
				},
				// {
				//     title: lan.site.other_ssl,
				//     callback: function (robj) {
				//         robj = $('#webedit-con .tab-con')
				//         var cert_info = '';
				//         if (rdata.cert_data['notBefore']) {
				//             cert_info = '<div style="margin-bottom: 10px;padding: 10px;" class="alert alert-success">\
				//                   <span style="display: inline-block;overflow: hidden;min-width: 49%;text-overflow: ellipsis;white-space: nowrap;max-width: 100%;">' + (rdata.status ? lan.site.deploy_success_tips : lan.site.not_deploy_and_save) + '</span>\
				//                   <span style="display: inline-block;overflow: hidden;min-width: 49%;text-overflow: ellipsis;white-space: nowrap;max-width: 100%;"><b>' + lan.site.cert_brand + '</b>' + rdata.cert_data.issuer + '</span>\
				//                   <span style="display:inline-block;max-width: 100%;min-width: 49%;overflow:hidden;text-overflow:ellipsis;white-space: nowrap; "><b>' + lan.site.auth_domain + '</b> ' + (rdata.cert_data.dns ? rdata.cert_data.dns.join(', ') : '') + '</span>\
				//                   <span style="display:inline-block;max-width: 100%;min-width: 49%;overflow:hidden;text-overflow:ellipsis;white-space: nowrap; "><b>' + lan.site.expire_time + '</b> ' + rdata.cert_data.notAfter + '</span></div>'
				//         }
				//         robj.append('<div>' + cert_info + '<div><span>' + lan.site.ssl_key + '</span><span style="padding-left:190px">' + lan.site.ssl_crt + '</span></div></div>');
				//         var datas = [{
				//             items: [
				//                 {name: 'key', width: '48%', height: '220px', type: 'textarea', value: rdata.key},
				//                 {name: 'csr', width: '48%', height: '220px', type: 'textarea', value: rdata.csr}
				//             ]
				//         },
				//             {
				//                 items: [{
				//                     text: lan.site.save,
				//                     name: 'btn_ssl_save',
				//                     type: 'button',
				//                     callback: function (sdata) {
				//                         bt.site.set_ssl(web.name, sdata, function (ret) {
				//                             if (ret.status) site.reload(7);
				//                             bt.msg(ret);
				//                         })
				//                     }
				//                 },
				//                     {
				//                         text: lan.site.ssl_close,
				//                         name: 'btn_ssl_close',
				//                         hide: !rdata.status,
				//                         type: 'button',
				//                         callback: function (sdata) {
				//                             site.ssl.set_ssl_status('CloseSSLConf', web.name);
				//                         }
				//                     }
				//                 ]
				//             }
				//         ]
				//         for (var i = 0; i < datas.length; i++) {
				//             var _form_data = bt.render_form_line(datas[i]);
				//             robj.append(_form_data.html);
				//             bt.render_clicks(_form_data.clicks);
				//         }
				//         var helps = [
				//             lan.site.bt_ssl_help_10,
				//             lan.public_backup.cret_err,
				//             lan.public_backup.pem_format,
				//             lan.site.ssl_tips5,
				//         ]
				//         robj.append(bt.render_help(helps));
				//         robj.find(".help-info-text").css('margin-top', '0');
				//         robj.find('textarea').css('resize', 'none');
				//         robj.find('[name=csr]').css('margin-right', '0');
				//     }
				// },
				// {
				//     title: lan.site.turn_off,
				//     callback: function (robj) {
				//         robj = $('#webedit-con .tab-con');
				//         if (rdata.type == -1) {
				//             robj.html("<div class='mtb15' style='line-height:30px'>" + lan.site.ssl_help_1 + "</div>");
				//         } else {
				//             var txt = '';
				//             switch (rdata.type) {
				//                 case 1:
				//                     txt = "Let's Encrypt";
				//                     break;
				//                 case 0:
				//                     txt = lan.site.other_ssl;
				//                     break;
				//                 case 2:
				//                     txt = lan.site.bt_ssl;
				//                     break;
				//             }
				//             robj.html('\
				//               <div class="line mtb15">' + lan.get('ssl_enable', [txt]) + '</div>\
				//               <div class="line mtb15">\
				//                   <button class="btn btn-success btn-sm" onclick="site.ssl.set_ssl_status(\'CloseSSLConf\', \'' + web.name + '\')">' + lan.site.ssl_close + '</button>\
				//               </div>\
				//           ');
				//         }
				//         var loadT = bt.load(lan.site.the_msg);
				//         $.post('/site?action=get_auto_restart_rph', {
				//             sitename: web.name
				//         }, function (res) {
				//             loadT.close();
				//             if (res) {
				//                 var checked_str = res.status ? 'checked="true"' : '';
				//                 robj.append('\
				//                 <div style="margin-bottom: 15px; border-top: #ccc 1px dashed;"></div>\
				//                   <div class="line">Auto restart proxy, redirect, http to https when apply or renew SSL</div>\
				//                   <div class="line">\
				//                       <input type="checkbox" class="btswitch btswitch-ios" id="auto_restart_rph" ' + checked_str + ' />\
				//                       <label class="btswitch-btn" for="closePl" onclick="site.ssl.set_auto_restart_rph(\'' + web.name + '\')"></label>\
				//                   </div>\
				//               ');
				//             }
				//         });
				//     }
				// },
				{
					title: lan.site.ssl_dir,
					callback: function (robj) {
						robj = $('#webedit-con .tab-con');
						robj.html("<div class='divtable' style='height:510px;'><table id='cer_list_table' class='table table-hover'></table></div>");
						bt.site.get_cer_list(function (rdata) {
							bt.render({
								table: '#cer_list_table',
								columns: [
									{
										field: 'subject',
										title: lan.site.domain,
										templet: function (item) {
											return item.dns.join('<br>');
										},
									},
									{ field: 'notAfter', width: '100px', title: lan.site.endtime },
									{ field: 'issuer', width: '150px', title: lan.site.brand },
									{
										field: 'opt',
										width: '100px',
										align: 'right',
										title: lan.site.operate,
										templet: function (item) {
											var opt =
												'<a class="btlink" onclick="bt.site.set_cert_ssl(\'' +
												item.subject +
												"','" +
												web.name +
												'\',function(rdata){if(rdata.status){site.ssl.reload(2);}})" href="javascript:;">' +
												lan.site.deploy +
												'</a> | ';
											opt +=
												'<a class="btlink" onclick="bt.site.remove_cert_ssl(\'' +
												item.subject +
												'\',function(rdata){if(rdata.status){site.ssl.reload(4);}})" href="javascript:;">' +
												lan.site.del +
												'</a>';
											return opt;
										},
									},
								],
								data: rdata,
							});
						});
					},
				},
			];

			bt.render_tab('ssl_tabs', tabs);

			// $('#ssl_tabs').append('<div class="ss-text pull-right mr30" style="position: relative;top:-4px"><em>' + lan.site.force_https + '</em><div class="ssh-item"><input class="btswitch btswitch-ios" id="toHttps" type="checkbox"><label class="btswitch-btn" for="toHttps"></label></div></div>');
			// $("#toHttps").attr('checked', rdata.httpTohttps);
			// $('#toHttps').click(function (sdata) {
			//     var isHttps = $("#toHttps").attr('checked');
			//     if (isHttps) {
			//         layer.confirm('After closing HTTPS, you need to clear your browser cache to see the effect. Continue?', {
			//             icon: 3,
			//             title: "Turn off forced HTTPS\""
			//         }, function () {
			//             bt.site.close_http_to_https(web.name, function (rdata) {
			//                 if (rdata.status) {
			//                     setTimeout(function () {
			//                         site.reload(7);
			//                     }, 3000);
			//                 }
			//             })
			//         });
			//     } else {
			//         bt.site.set_http_to_https(web.name, function (rdata) {
			//             if (!rdata.status) {
			//                 setTimeout(function () {
			//                     site.reload(7);
			//                 }, 3000);
			//             }

			//         })
			//     }
			// })
			// switch (rdata.type) {
			//     case 1:
			//         $('#ssl_tabs span:eq(0)').trigger('click');
			//         break;
			//     case 0:
			//         $('#ssl_tabs span:eq(0)').trigger('click');
			//         break;
			//     default:
			//         $('#ssl_tabs span:eq(0)').trigger('click');
			//         break;
			// }

			$('#ssl_tabs span:eq(' + (rdata.status ? (rdata.csr ? 0 : 1) : 1) + ')').trigger('click');

			$('.cutTabView').on('click', function () {
				$('#ssl_tabs span:eq(1)').trigger('click');
				setTimeout(function () {
					$('.ssl_business_application').trigger('click');
				}, 400);
			});
		});
	},
	show_certificate_confirm: function (sitename, callback) {
		var _this = this;
		var auto_restart_rph = function (index, loading) {
			if (loading) loadT = bt.load(lan.site.the_msg);
			$.post(
				'/site?action=auto_restart_rph',
				{
					sitename: sitename,
				},
				function (res) {
					loadT.close();
					if (res.status) {
						if (index) layer.close(index);
						if (callback) callback(res);
					}
				}
			);
		};
		var loadT = bt.load(lan.site.the_msg);
		$.post(
			'/site?action=get_auto_restart_rph',
			{
				sitename: sitename,
			},
			function (res) {
				if (res && res.status) {
					auto_restart_rph();
				} else {
					loadT.close();
					layer.open({
						type: 1,
						area: '530px',
						title: 'Apply SSL',
						closeBtn: 2,
						shift: 5,
						shadeClose: false,
						content:
							'\
                      <div class="bt-form pd20 pd70 ssl_cert_from" style="padding: 20px 35px 60px;">\
                          <div>\
                    <i class="layui-layer-ico layui-layer-ico3"></i>\
                    <h3 style="margin-left: 60px;">Apply or renew SSL</h3>\
                    <ul style="width: 90%; margin-bottom: 20px; margin-top: 20px;">\
                      <li style="height: auto;">The reverse proxy, redirection and http to https will be automatically restart during the application or renewal of SSL!</li>\
                      <li style="height: auto;">The application and renewal of SSL will not be affected by the redirection, reverse proxy and http to https</li>\
                    </ul>\
                  </div>\
                  <div class="bt-form-submit-btn">\
                    <button type="button" class="btn btn-sm btn-danger close_cert">Just apply</button>\
                    <button type="button" class="btn btn-sm btn-success submit_cert">Apply and open</button>\
                  </div>\
                      </div>\
                  ',
						success: function (layers, index) {
							$('.submit_cert').click(function () {
								auto_restart_rph(index, true);
							});
							$('.close_cert').click(function () {
								layer.close(index);
							});
						},
					});
				}
			}
		);
	},
};

$('#cutMode .tabs-item[data-type="' + (bt.get_cookie('site_model') || 'php') + '"]').trigger('click');
// site.get_types();

// $.prototype.serializeObject = function() {
// 	var a, o, h, i, e;
// 	a = this.serializeArray();
// 	o = {};
// 	h = o.hasOwnProperty;
// 	for (i = 0; i < a.length; i++) {
// 		e = a[i];
// 		if (!h.call(o, e.name)) {
// 			o[e.name] = e.value;
// 		}
// 	}
// 	return o;
// };
