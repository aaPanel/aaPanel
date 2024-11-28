var __extends =
	(this && this.__extends) ||
	(function () {
		var extendStatics = function (d, b) {
			extendStatics =
				Object.setPrototypeOf ||
				({ __proto__: [] } instanceof Array &&
					function (d, b) {
						d.__proto__ = b;
					}) ||
				function (d, b) {
					for (var p in b) if (Object.prototype.hasOwnProperty.call(b, p)) d[p] = b[p];
				};
			return extendStatics(d, b);
		};
		return function (d, b) {
			if (typeof b !== 'function' && b !== null) throw new TypeError('Class extends value ' + String(b) + ' is not a constructor or null');
			extendStatics(d, b);
			function __() {
				this.constructor = d;
			}
			d.prototype = b === null ? Object.create(b) : ((__.prototype = b.prototype), new __());
		};
	})();
var __awaiter =
	(this && this.__awaiter) ||
	function (thisArg, _arguments, P, generator) {
		function adopt(value) {
			return value instanceof P
				? value
				: new P(function (resolve) {
						resolve(value);
				  });
		}
		return new (P || (P = Promise))(function (resolve, reject) {
			function fulfilled(value) {
				try {
					step(generator.next(value));
				} catch (e) {
					reject(e);
				}
			}
			function rejected(value) {
				try {
					step(generator['throw'](value));
				} catch (e) {
					reject(e);
				}
			}
			function step(result) {
				result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected);
			}
			step((generator = generator.apply(thisArg, _arguments || [])).next());
		});
	};
var __generator =
	(this && this.__generator) ||
	function (thisArg, body) {
		var _ = {
				label: 0,
				sent: function () {
					if (t[0] & 1) throw t[1];
					return t[1];
				},
				trys: [],
				ops: [],
			},
			f,
			y,
			t,
			g;
		return (
			(g = { next: verb(0), throw: verb(1), return: verb(2) }),
			typeof Symbol === 'function' &&
				(g[Symbol.iterator] = function () {
					return this;
				}),
			g
		);
		function verb(n) {
			return function (v) {
				return step([n, v]);
			};
		}
		function step(op) {
			if (f) throw new TypeError('Generator is already executing.');
			while (_)
				try {
					if (((f = 1), y && (t = op[0] & 2 ? y['return'] : op[0] ? y['throw'] || ((t = y['return']) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done)) return t;
					if (((y = 0), t)) op = [op[0] & 2, t.value];
					switch (op[0]) {
						case 0:
						case 1:
							t = op;
							break;
						case 4:
							_.label++;
							return { value: op[1], done: false };
						case 5:
							_.label++;
							y = op[1];
							op = [0];
							continue;
						case 7:
							op = _.ops.pop();
							_.trys.pop();
							continue;
						default:
							if (!((t = _.trys), (t = t.length > 0 && t[t.length - 1])) && (op[0] === 6 || op[0] === 2)) {
								_ = 0;
								continue;
							}
							if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) {
								_.label = op[1];
								break;
							}
							if (op[0] === 6 && _.label < t[1]) {
								_.label = t[1];
								t = op;
								break;
							}
							if (t && _.label < t[2]) {
								_.label = t[2];
								_.ops.push(op);
								break;
							}
							if (t[2]) _.ops.pop();
							_.trys.pop();
							continue;
					}
					op = body.call(thisArg, _);
				} catch (e) {
					op = [6, e];
					y = 0;
				} finally {
					f = t = 0;
				}
			if (op[0] & 5) throw op[1];
			return { value: op[0] ? op[1] : void 0, done: true };
		}
	};
var __spreadArray =
	(this && this.__spreadArray) ||
	function (to, from, pack) {
		if (pack || arguments.length === 2)
			for (var i = 0, l = from.length, ar; i < l; i++) {
				if (ar || !(i in from)) {
					if (!ar) ar = Array.prototype.slice.call(from, 0, i);
					ar[i] = from[i];
				}
			}
		return to.concat(ar || Array.prototype.slice.call(from));
	};
var __importDefault =
	(this && this.__importDefault) ||
	function (mod) {
		return mod && mod.__esModule ? mod : { default: mod };
	};
define(['require', 'exports', './snabbdom', './public/public', './panelConfig', './safeConfig', './noticeConfig'], function (
	require,
	exports,
	snabbdom_1,
	public_1,
	panelConfig_1,
	safeConfig_1,
	noticeConfig_1
) {
	'use strict';
	Object.defineProperty(exports, '__esModule', { value: true });
	exports.Config = void 0;
	public_1 = __importDefault(public_1);
	panelConfig_1 = __importDefault(panelConfig_1);
	safeConfig_1 = __importDefault(safeConfig_1);
	noticeConfig_1 = __importDefault(noticeConfig_1);
	var panelConfig = new panelConfig_1.default();
	var safeConfig = new safeConfig_1.default();
	var noticeConfig = new noticeConfig_1.default();
	var Config = (function (_super) {
		__extends(Config, _super);
		function Config() {
			var _this = _super.call(this) || this;
			_this.Info = {};
			_this.configInfo = {};
			_this.formInfo = {};
			_this.alertListModule = {};
			_this.panelSiteList = [];
			_this.taskTypeList = [
				{ title: 'Website certificate (SSL) expires', value: 'ssl', model: 'site_push' },
				{ title: 'Website expiration', value: 'site_endtime', model: 'site_push' },
				{ title: 'Panel password validity period', value: 'panel_pwd_endtime', model: 'site_push' },
				{ title: 'Panel login alarm', value: 'panel_login', model: 'site_push' },
				{ title: 'SSH login alarm', value: 'ssh_login', model: 'site_push' },
				{ title: 'SSH login failure alarm', value: 'ssh_login_error', model: 'site_push' },
				{ title: 'Panel security alarm', value: 'panel_safe_push', model: 'site_push' },
				// { title: 'Panel update reminder', value: 'panel_update', model: 'site_push' },
			];
			_this.disabledOption = ['site_endtime', 'ssh_login', 'ssh_login_error', 'panel_login', 'panel_pwd_endtime', 'panel_safe_push', 'panel_update'];
			_this.apiInfo = {
				getConfig: ['config/get_config', lan.public.the],
				getCheckTwoStep: ['config/check_two_step', lan.public.the],
				getPasswordConfig: ['config/get_password_config', 'Getting the password complexity verification status, please wait...'],
				getMenuList: ['config/get_menu_list', 'Getting panel menu bar, please wait...'],
				getMessageChannel: ['config/get_msg_configs', 'Getting profile, please wait...'],
				getLoginAlarm: ['config/get_login_send', 'Getting login information, please wait...'],
				setMsgConfigmail: ['config/set_msg_config&name=mail', 'Setting recipient email'],
				setPanelConfig: ['config/setPanel', lan.config.config_save],
			};
			_this.alertConfigForm = [
				{
					label: 'Task type',
					group: {
						type: 'select',
						name: 'type',
						width: '250px',
						value: 'ssl',
						class: 'projectBox',
						list: _this.taskTypeList,
						disabled: false,
						change: function (formData, element, that) {
							var config = _this.switchPushType(that.config.form, formData);
							that.$again_render_form(config);
						},
					},
				},
				{
					label: 'Website',
					group: {
						type: 'select',
						name: 'site',
						width: '250px',
						value: '',
						list: [],
					},
				},
				{
					label: 'Remaining days',
					group: {
						type: 'number',
						name: 'cycle',
						width: '70px',
						unit: 'Day(s)',
						value: 1,
					},
				},
				{
					label: 'Cycle',
					hide: true,
					group: [
						{
							type: 'number',
							name: 'where1',
							width: '70px',
							value: 30,
							unit: 'Minute(s) <div style="display: inline-block; color: #333; margin-left: 30px;">Frequency</div>',
							input: function (data, b, c, d, e) {
								var $input = $(e.currentTarget);
								var num = $input.val();
								if (num < 0) {
									$input.val(0);
									num = 0;
								}
								var text = ''.concat(num, ' minute').concat(num > 1 ? 's' : '');
								$('.condition_tips').find('.minute').text(text);
							},
						},
						{
							type: 'number',
							name: 'count',
							width: '50px',
							style: { 'vertical-align': 'initial', 'margin-left': '10px' },
							value: 3,
							unit: 'Time(s) ',
							input: function (data, b, c, d, e) {
								var $input = $(e.currentTarget);
								var num = $input.val();
								if (num < 0) {
									$input.val(0);
									num = 0;
								}
								var text = ''.concat(num, ' time').concat(num > 1 ? 's' : '');
								$('.condition_tips').find('.time').text(text);
							},
						},
						{
							type: 'div',
							dispaly: 'block',
							class: 'condition_tips',
							style: { 'margin-top': '10px', color: '#666' },
							content: 'Login failed <span class="time">3 times</span> within <span class="minute">30 minutes</span>',
						},
					],
				},
				{
					label: 'Interval',
					group: {
						type: 'number',
						name: 'interval',
						width: '70px',
						value: 600,
						unit: 'second(s)<div style="margin-top: 12px;">Monitor the trigger condition again after an interval of <span class="count">600 seconds</span></div>',
						input: function (data, b, c, d, e) {
							var $input = $(e.currentTarget);
							var num = $input.val();
							if (num < 0) {
								$input.val(0);
								num = 0;
							}
							var text = ''.concat(num, ' second').concat(num > 1 ? 's' : '');
							$input.next().find('.count').text(text);
						},
					},
				},
				{
					label: 'Send times',
					group: {
						type: 'number',
						name: 'push_count',
						width: '70px',
						value: 1,
						unit: 'Time(s)<div style="margin-top: 12px;">After sending <span class="count">1 time</span>, no more alarm messages will be sent, <br />if you want to send multiple times, please fill in more than 2 times.</div>',
						input: function (data, b, c, d, e) {
							var $input = $(e.currentTarget);
							var num = $input.val();
							if (num < 0) {
								$input.val(0);
								num = 0;
							}
							var text = ''.concat(num, ' time').concat(num > 1 ? 's' : '');
							$input.next().find('.count').text(text);
						},
					},
				},
				{
					label: 'Alarm mode',
					group: [],
				},
				{
					label: 'Alarm content',
					hide: true,
					group: {
						type: 'help',
						style: { 'margin-top': '6px' },
						list: ['panel user change, panel log delete, panel open developer, panel open API'],
					},
				},
				{
					label: '',
					group: {
						type: 'button',
						name: 'submitForm',
						title: 'Add task',
						event: function (formData, element, that) {
							that.submit(formData);
						},
					},
				},
			];
			_this.init();
			return _this;
		}
		Config.prototype.init = function () {
			return __awaiter(this, void 0, void 0, function () {
				return __generator(this, function (_a) {
					this.$apiInit(this.apiInfo);
					this.render();
					this.event();
					return [2];
				});
			});
		};
		Config.prototype.render = function () {
			var _this = this;
			var loadT = this.$load(lan.public.the);
			Promise.all([
				this.$request('getConfig', false),
				this.$request('getCheckTwoStep', { loading: false, msg: false }),
				this.$request('getPasswordConfig', { loading: false, msg: false }),
				this.$request('getUserInfo', { loading: false, msg: false }),
				this.$request('getMessageChannel', { loading: false, msg: false }),
				this.$request('getLoginAlarm', { loading: false, msg: false }),
				this.$request('getMenuList', { loading: false, msg: false }),
			])
				.then(function (resArr) {
					var configInfo = resArr[0],
						twoStep = resArr[1],
						pawComplexity = resArr[2],
						bindUserInfo = resArr[3],
						messageChannelInfo = resArr[4],
						loginAlarmInfo = resArr[5],
						menuList = resArr[6];
					panelConfig.init({ configInfo: configInfo, menuList: menuList, bindUserInfo: bindUserInfo });
					safeConfig.init({ configInfo: configInfo, twoStep: twoStep, pawComplexity: pawComplexity });
					noticeConfig.init({ messageChannelInfo: messageChannelInfo, loginAlarmInfo: loginAlarmInfo });
				})
				.catch(function (err) {
					console.log(err);
					_this.$error(err.msg || 'Server Error');
				})
				.finally(function () {
					loadT.close();
				});
		};
		Config.prototype.event = function () {
			var _this = this;
			$('#configTab').on('click', '.tabs-item', function (ev) {
				var el = $(ev.currentTarget);
				var type = el.attr('data-type');
				el.addClass('active').siblings().removeClass('active');
				$('.configure-box .panel-config').addClass('hide');
				if (type === 'allConfig') {
					$('.configure-box .panel-config:not(.alert-view-box)').removeClass('hide');
				} else {
					if (type === 'alertConfig') _this.renderAlertView();
					$('.configure-box .panel-config[data-type="' + type + '"]').removeClass('hide');
				}
				_this.$setCookie('config-tab', type);
			});
			this.cateClick();
			$('input[type="text"]').on('input', function (ev) {
				return __awaiter(_this, void 0, void 0, function () {
					var el, value, oldValue;
					return __generator(this, function (_a) {
						el = $(ev.target);
						value = el.val();
						oldValue = el.attr('value');
						value != oldValue ? el.parent().next().removeAttr('disabled') : el.parent().next().attr('disabled', 'disabled');
						return [2];
					});
				});
			});
			$('.savePanelConfig').click(function () {
				return __awaiter(_this, void 0, void 0, function () {
					var data, res, href;
					return __generator(this, function (_a) {
						switch (_a.label) {
							case 0:
								data = this.getInputData();
								return [4, this.$request('setPanelConfig', data)];
							case 1:
								res = _a.sent();
								href = '';
								if (data.domain) {
									href = window.location.protocol + '//' + data.domain + ':' + window.location.port + window.location.pathname;
								} else {
									href = window.location.protocol + '//' + data.address + ':' + window.location.port + window.location.pathname;
								}
								res.status && this.$refreshBrowser();
								return [2];
						}
					});
				});
			});
			$('.setPanelPort').click(function () {
				return _this.setPanelPortView();
			});
			$('#addAlertTask').on('click', '.alertInstall', function (ev) {
				var _type = $(ev.currentTarget).parent('span').siblings('input').attr('name');
				_this.setAlertConfigType(_type);
			});

			setTimeout(function () {
				$.fn.serializeObject = function () {
					var hasOwnProperty = Object.prototype.hasOwnProperty;
					return this.serializeArray().reduce(function (data, pair) {
						if (!hasOwnProperty.call(data, pair.name)) {
							data[pair.name] = pair.value;
						}
						return data;
					}, {});
				};
			}, 300);

			panelConfig.event();
			safeConfig.event();
			noticeConfig.event();
		};
		Config.prototype.cateClick = function () {
			var configTab = this.$getCookie('config-tab') || 'allConfig';
			if (!isNaN(Number(configTab))) {
				configTab = 'allConfig';
			}
			$('#configTab .tabs-item[data-type="' + configTab + '"]').trigger('click');
		};
		Config.prototype.setPanelPortView = function () {
			var _this = this;
			var $input = $('input[name="port"]');
			var port = $input.val();
			this.$open({
				title: 'Change Panel Port',
				area: ['380px', '380px'],
				btn: ['Confirm', 'Cancel'],
				content: {
					data: { port: port, agreement: false },
					template: function () {
						return (0, snabbdom_1.jsx)(
							'div',
							{ class: this.$class('pd20 bt-form') },
							this.$ul({ className: 'explainDescribeList', style: 'margin-top:0;' }, [
								['1. Have a security group server, please release the new port in the security group in advance.', 'red'],
								['2. If the panel is inaccessible after modifying the port, change the original port to the SSH command line by using the bt command.', 'red'],
							]),
							this.$line({ title: 'Port', width: '60px' }, this.$input({ model: 'port', width: '210px' })),
							this.$learnMore({
								title: (0, snabbdom_1.jsx)(
									'span',
									null,
									'I already understand, ',
									this.$link({ title: 'How to release the port?', href: 'https://www.aapanel.com/forum/d/599-how-to-release-the-aapanel-port' })
								),
								model: 'agreement',
								id: 'checkPanelPort',
							})
						);
					},
				},
				yes: function (content) {
					return __awaiter(_this, void 0, void 0, function () {
						var close, vm, port, data, rdata;
						return __generator(this, function (_a) {
							switch (_a.label) {
								case 0:
									(close = content.close), (vm = content.vm), (port = parseInt(vm.port));
									if (!vm.agreement) return [2, this.$tips({ el: '#checkPanelPort', msg: 'Please tick the one I already know' })];
									return [4, this.$verifySubmit(!this.$checkPort(port), 'Please enter correct panel port!')];
								case 1:
									_a.sent();
									data = this.getInputData();
									data.port = port;
									return [4, this.$request('setPanelConfig', data)];
								case 2:
									rdata = _a.sent();
									if (rdata.status) {
										close();
										this.$refreshBrowser(''.concat(location.protocol, '//').concat(location.hostname, ':').concat(port).concat(location.pathname));
									}
									return [2];
							}
						});
					});
				},
			}).catch(function (err) {});
		};
		Config.prototype.getInputData = function () {
			var data = {};
			$('.savePanelConfig').each(function (index, item) {
				var $input = $(item).parents('.line').find('input[type="text"]');
				var key = $input.attr('name');
				var value = $input.val();
				data[key] = value;
			});
			return data;
		};
		Config.renderFormColumn = function (configInfo) {
			for (var key in configInfo) {
				if (Object.prototype.hasOwnProperty.call(configInfo, key)) {
					var value = configInfo[key].value;
					var el = $('input[name="' + key + '"]');
					var type = el.attr('type');
					if (type === 'checkbox') {
						el.prop('checked', value);
					} else {
						el.val(value);
					}
				}
			}
		};
		Config.prototype.renderAlertView = function () {
			return __awaiter(this, void 0, void 0, function () {
				var _this = this;
				return __generator(this, function (_a) {
					this.alertTaskList();
					$('.alert-view-box')
						.unbind('click')
						.on('click', '.tab-nav-border span', function (ev) {
							var el = $(ev.currentTarget),
								index = $(el).index();
							$(el).addClass('on').siblings().removeClass('on');
							$(el).parent().next().find('.tab-block').eq(index).addClass('on').siblings().removeClass('on');
							switch (index) {
								case 0:
									_this.alertTaskList();
									break;
								case 1:
									_this.alertConfigTable();
									break;
								case 2:
									_this.alertLogsTable();
									break;
							}
						});
					return [2];
				});
			});
		};
		Config.prototype.alertTaskList = function () {
			return __awaiter(this, void 0, void 0, function () {
				var ChannelMessage, resetChannelMessage, prevArray, _a;
				return __generator(this, function (_b) {
					switch (_b.label) {
						case 0:
							return [4, this.$request('getMessageChannel', { loading: false, msg: false })];
						case 1:
							ChannelMessage = _b.sent();
							resetChannelMessage = [];
							prevArray = [];
							Object.getOwnPropertyNames(ChannelMessage).forEach(function (key) {
								var mod = ChannelMessage[key];
								key == 'wx_account' ? prevArray.push(mod) : resetChannelMessage.push(mod);
							});
							this.alertListModule = __spreadArray(__spreadArray([], prevArray, true), resetChannelMessage, true);
							_a = this;
							return [4, this.$request(['crontab/GetDataList'], { type: 'sites' })];
						case 2:
							_a.panelSiteList = _b.sent();
							return [4, this.addAlertTask()];
						case 3:
							_b.sent();
							this.renderAlarmList();
							return [2];
					}
				});
			});
		};
		Config.prototype.addAlertTask = function () {
			return __awaiter(this, void 0, void 0, function () {
				var _config;
				var _this = this;
				return __generator(this, function (_a) {
					_config = this.switchPushType(__spreadArray([], this.alertConfigForm, true));
					bt_tools.form({
						el: '#addAlertTask',
						form: _config,
						submit: function (formData) {
							_this.setAlertConfigTask(formData);
						},
					});
					return [2];
				});
			});
		};
		Config.prototype.renderAlarmList = function () {
			var _this = this;
			$('#alertList').empty();
			var alertListTabel = bt_tools.table({
				el: '#alertList',
				url: '/push?action=get_push_list',
				default: 'The alarm list is empty',
				autoHeight: true,
				height: 320,
				dataFilter: function (res) {
					$.each(res.site_push, function (index, item) {
						item['id'] = index;
					});
					var data = Object.values(res.site_push || []);
					return { data: data };
				},
				column: [
					{
						type: 'checkbox',
						width: 20,
					},
					{
						fid: 'title',
						title: 'Title',
						type: 'text',
						template: function (row) {
							var _title = '';
							switch (row.type) {
								case 'ssl':
									_title = '['.concat(row.project == 'all' ? 'All' : row.project, ']').concat(row.title);
									break;
								default:
									_title = row.title;
									break;
							}
							return '<span>'.concat(_title, '</span>');
						},
					},
					{
						fid: 'status',
						title: 'Status',
						config: {
							icon: true,
							list: [
								[true, 'Normal', 'bt_success', 'glyphicon-play'],
								[false, 'Suspend', 'bt_danger', 'glyphicon-pause'],
							],
						},
						type: 'status',
						event: function (row) {
							return __awaiter(_this, void 0, void 0, function () {
								var param, eData, rdata;
								return __generator(this, function (_a) {
									switch (_a.label) {
										case 0:
											if (row.type == 'ssh_login') return [2, layer.msg('Do not support suspend SSH login alarm, if you want to stop it, please delete it directly.', { icon: 0 })];
											(param = {}), (eData = $.extend(true, row, { status: row.status ? false : true }));
											param['name'] = row.module_type;
											param['id'] = row.id;
											param['data'] = JSON.stringify(eData);
											return [4, this.$request(['push/set_push_config', 'Setting alarm tasks'], param)];
										case 1:
											rdata = _a.sent();
											if (!rdata.status) return [3, 3];
											return [4, this.alertTaskList()];
										case 2:
											_a.sent();
											_a.label = 3;
										case 3:
											return [2];
									}
								});
							});
						},
					},
					{
						title: 'Alarm mode',
						type: 'text',
						width: 265,
						template: function (row) {
							var alertMode = row.module.split(','),
								_mode = '';
							_this.alertListModule.forEach(function (mod) {
								if ($.inArray(mod.name, alertMode) >= 0) _mode += mod.title + ',';
							});
							_mode = _mode.substring(0, _mode.length - 1);
							return '<span>' + _mode + '</span>';
						},
					},
					{
						fid: 'cycle',
						title: 'Alarm condition',
						template: function (row) {
							switch (row.type) {
								case 'ssl':
								case 'site_endtime':
								case 'panel_pwd_endtime':
									return '<span>Less than '
										.concat(row.cycle, ' days remaining ')
										.concat(typeof row.push_count != 'undefined' ? '(If not processed, it will be resent 1 time the next day for ' + row.push_count + ' days)' : '', '</span>');
								case 'ssh_login_error':
									return '<span>Triggered by '
										.concat(row.count, ' consecutive failed login attempts within ')
										.concat(row.cycle, ' minutes, to be detected again after every ')
										.concat(row.interval, ' seconds</span>');
								case 'panel_update':
									return '<span>Send a notification when a new version is detected</span>';
								default:
									return '--';
							}
						},
					},
					{
						title: lan.public.operate,
						type: 'group',
						width: 150,
						align: 'right',
						group: [
							{
								title: lan.public.edit,
								event: function (row) {
									_this.setAlertTaskConfig(row);
								},
							},
							{
								title: lan.public.del,
								event: function (row) {
									return __awaiter(_this, void 0, void 0, function () {
										var rdata;
										return __generator(this, function (_a) {
											switch (_a.label) {
												case 0:
													return [
														4,
														this.$confirm({
															title: 'Delete Alarm Tasks',
															msg: 'Delete will no longer alert this task, do you want to continue?',
														}),
													];
												case 1:
													_a.sent();
													return [4, this.$request(['push/del_push_config', 'Deleting the alarm task'], { name: row.module_type, id: row.id })];
												case 2:
													rdata = _a.sent();
													if (!rdata.status) return [3, 4];
													return [4, this.alertTaskList()];
												case 3:
													_a.sent();
													_a.label = 4;
												case 4:
													return [2];
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
						type: 'batch',
						positon: ['left', 'bottom'],
						config: {
							title: ' Delete',
							url: 'push?action=del_push_config',
							load: true,
							param: function (row) {
								return { name: row.module_type, id: row.id };
							},
							callback: function (that) {
								bt.confirm({ title: 'Batch Delete Tasks', msg: 'The batch deletion will not be recovered, does it continue?', icon: 0 }, function (index) {
									layer.close(index);
									that.start_batch({}, function (list) {
										var html = '';
										for (var i = 0; i < list.length; i++) {
											var item = list[i];
											html +=
												'<tr><td>' +
												(typeof item.project == 'undefined' ? item.title : (item.project == 'all' ? 'All' : item.project) + item.title) +
												'</td><td><div style="float:right;"><span style="color:' +
												(item.request.status ? '#20a53a' : 'red') +
												'">' +
												item.request.msg +
												'</span></div></td></tr>';
										}
										alertListTabel.$batch_success_table({ title: 'Batch Delete Tasks', th: 'Task title', html: html });
										alertListTabel.$refresh_table_list(true);
									});
								});
							},
						},
					},
				],
			});
		};
		Config.prototype.setAlertTaskConfig = function (row) {
			return __awaiter(this, void 0, void 0, function () {
				var _config;
				var _this = this;
				return __generator(this, function (_a) {
					_config = this.switchPushType($.extend(true, {}, this.alertConfigForm), row);
					_config[0].group.disabled = true;
					_config[0].group.unit = '';
					_config[8].hide = true;
					if (row.type == 'ssh_login_error') {
						row.where1 = row.cycle;
					}
					bt_tools.open({
						type: 1,
						title: 'Edit Alert Tasks',
						area: '540px',
						skin: 'panel_alert_task_view',
						btn: [lan.public.save, lan.public.cancel],
						content: {
							class: 'pd15',
							data: row,
							form: _config,
						},
						success: function (layers) {
							$(layers)
								.find('.layui-layer-content')
								.css('overflow', window.innerHeight > $(layers).height() ? 'inherit' : 'auto');
							$('.alertInstall').click(function (ev) {
								var _type = $(ev.currentTarget).parent('span').siblings('input').attr('name');
								_this.setAlertConfigType(_type);
							});
						},
						yes: function (formData, index) {
							_this.setAlertConfigTask($.extend(true, {}, row, formData), index);
						},
					});
					return [2];
				});
			});
		};
		Config.prototype.setAlertConfigTask = function (row, close) {
			if (close === void 0) {
				close = null;
			}
			return __awaiter(this, void 0, void 0, function () {
				var _configD, eData, pushType, otherType, isCheck, rdata;
				return __generator(this, function (_a) {
					switch (_a.label) {
						case 0:
							(_configD = {}),
								(eData = {}),
								(pushType = this.taskTypeList.find(function (el) {
									return el.value == row.type;
								})),
								(otherType = this.disabledOption);
							_configD['name'] = typeof row.module_type !== 'undefined' ? row.module_type : pushType.model;
							_configD['id'] = row.id ? row.id : $.inArray(row.type, otherType) >= 0 ? row.type : new Date().getTime();
							eData['interval'] = 600;
							switch (row.type) {
								case 'ssl':
								case 'site_endtime':
								case 'panel_pwd_endtime':
									if (row.type == 'ssl') eData['project'] = row.site || 'all';
									if (row.cycle == '' || row.cycle < 0) return [2, this.$msg({ icon: 2, msg: 'Remaining days cannot be less than 1', time: 0, closeBtn: 2 })];
									eData['cycle'] = Number(row.cycle);
									eData['push_count'] = Number(row.push_count);
									break;
								case 'ssh_login_error':
									if (row.where1 == '' || row.where1 <= 0) return [2, this.$msg({ icon: 2, msg: 'Trigger time cannot be less than 1', time: 0, closeBtn: 2 })];
									if (row.count == '' || row.count <= 0) return [2, this.$msg({ icon: 2, msg: 'Trigger times cannot be less than 1', time: 0, closeBtn: 2 })];
									if (row.interval == '' || row.interval <= 0) return [2, this.$msg({ icon: 2, msg: 'Interval cannot be less than 1', time: 0, closeBtn: 2 })];
									eData['cycle'] = Number(row.where1);
									eData['count'] = Number(row.count);
									eData['interval'] = Number(row.interval);
									break;
							}
							isCheck = [];
							$((row.id ? '.panel_alert_task_view ' : '#addAlertTask ') + '.module-check')
								.not('.check_disabled')
								.each(function () {
									if ($(this).find('input').prop('checked')) {
										isCheck.push($(this).find('input').prop('name'));
									}
								});
							eData['type'] = row.type;
							eData['module'] = isCheck.join();
							if (typeof eData['push_count'] != 'undefined' && (eData['push_count'] <= 0 || eData['push_count'] == '')) {
								this.$msg({ icon: 2, msg: 'The number of sending cannot be less than 1', time: 0, closeBtn: 2 });
								return [2, false];
							}
							if (!eData['module']) {
								this.$msg({ icon: 2, msg: 'Please select an alarm mode', time: 0, closeBtn: 2 });
								return [2, false];
							}
							eData['status'] = typeof row.status !== 'undefined' ? row.status : true;
							eData['title'] = $((row.id ? '.panel_alert_task_view ' : '#addAlertTask ') + '.projectBox .bt_select_content').html();
							_configD['data'] = JSON.stringify(eData);
							return [4, this.$request(['push/set_push_config', 'Setting alarm task, Please wait...'], _configD)];
						case 1:
							rdata = _a.sent();
							if (!rdata.status) return [3, 3];
							layer.close(close);
							return [4, this.alertTaskList()];
						case 2:
							_a.sent();
							_a.label = 3;
						case 3:
							return [2];
					}
				});
			});
		};
		Config.prototype.switchPushType = function (config, formData) {
			if (formData === void 0) {
				formData = {};
			}
			var _checklist = [],
				isCheckType = [],
				siteList = [{ title: 'All Website', value: 'all' }],
				accountConfigStatus = false;
			if (!formData.type) {
				formData.type = 'ssl';
				config[1].group.value = 'all';
			}
			this.panelSiteList['data'].forEach(function (key) {
				siteList.push({ title: key.name, value: key.name });
			});
			this.alertListModule.forEach(function (mod, i) {
				if (formData.type != 'ssl' && mod.name == 'sms') return;
				if (formData.module) {
					isCheckType = formData.module.split(',');
				}
				if (mod.name === 'wx_account') {
					if (!$.isEmptyObject(mod.data) && mod.data.res.is_subscribe && mod.data.res.is_bound) {
						accountConfigStatus = true;
					}
				}
				_checklist.push({
					type: 'checkbox',
					name: mod.name,
					class: 'module-check ' + (!mod.setup || $.isEmptyObject(mod.data) ? 'check_disabled' : mod.name == 'wx_account' && !accountConfigStatus ? 'check_disabled' : '') + '',
					style: { 'margin-right': '10px' },
					disabled: !mod.setup || $.isEmptyObject(mod.data) ? true : mod.name == 'wx_account' && !accountConfigStatus ? true : false,
					value: $.inArray(mod.name, isCheckType) >= 0 ? 1 : 0,
					title:
						(mod.name == 'wx_account' ? '<b style="color: #fc6d26;"> [Recommend]</b>' : '') +
						mod.title +
						(!mod.setup || $.isEmptyObject(mod.data)
							? '<span style="color:red;cursor: pointer;" class="alertInstall"> [Install]</span>'
							: mod.name == 'wx_account' && !accountConfigStatus
							? ' [<a target="_blank" class="bterror alertInstall">Not set</a>]'
							: ''),
					event: function (formData, element, thatE) {
						thatE.config.form[6].group[i].value = !formData[mod.name] ? 0 : 1;
					},
				});
			});
			if (!formData.id) {
				var checkActive = _checklist.findIndex(function (ev) {
					return !ev.disabled;
				});
				if (checkActive >= 0) _checklist[checkActive].value = 1;
			} else {
				if (formData.type == 'ssl') config[1].group.value = formData.project;
			}
			config[1].hide = true;
			config[3].hide = true;
			config[4].hide = true;
			config[5].hide = false;
			delete config[0].group.unit;
			switch (formData.type) {
				case 'ssl':
					config[1].hide = false;
					config[2].hide = false;
					config[2].group.value = 15;
					break;
				case 'site_endtime':
					config[2].hide = false;
					config[2].group.value = 7;
					break;
				case 'panel_pwd_endtime':
					config[2].hide = false;
					config[2].group.value = 15;
					break;
				case 'panel_login':
				case 'ssh_login':
				case 'panel_safe_push':
				case 'panel_update':
					config[2].hide = true;
					config[5].hide = true;
					if (formData.type == 'panel_update') {
						config[0].group.unit = '* Send a notification when a new version is detected';
					}
					break;
				case 'ssh_login_error':
					config[2].hide = true;
					config[3].hide = false;
					config[4].hide = false;
					config[5].hide = true;
					break;
			}
			config[7].hide = formData.type === 'panel_safe_push' ? false : true;
			config[0].group.value = formData.type;
			config[1].group.list = siteList;
			config[6].group = _checklist;
			return config;
		};
		Config.prototype.setAlertConfigType = function (type) {
			return __awaiter(this, void 0, void 0, function () {
				var _configData;
				return __generator(this, function (_a) {
					switch (_a.label) {
						case 0:
							return [4, this.$request('getMessageChannel', { loading: false, msg: false })];
						case 1:
							_configData = _a.sent();
							switch (type) {
								case 'mail':
									renderMailConfigView(_configData[type]);
									break;
								case 'dingding':
								case 'feishu':
								case 'weixin':
									renderAlertUrlTypeChannelView(_configData[type]);
									break;
								case 'tg':
									renderTelegramConfigView(_configData[type]);
									break;
							}
							return [2];
					}
				});
			});
		};
		Config.prototype.alertConfigTable = function () {
			return __awaiter(this, void 0, void 0, function () {
				var ChannelInfo, html, tbody, prevHTML;
				var _this = this;
				return __generator(this, function (_a) {
					switch (_a.label) {
						case 0:
							return [4, this.$request('getMessageChannel', { loading: false, msg: false })];
						case 1:
							ChannelInfo = _a.sent();
							(html = ''), (tbody = ''), (prevHTML = '');
							$('#alertConfig').empty();
							Object.getOwnPropertyNames(ChannelInfo).forEach(function (key) {
								var item = ChannelInfo[key],
									btnGroup = '';
								if (item.setup) {
									if (item.name != 'sms') {
										if (!$.isEmptyObject(item.data)) {
											if (item.name == 'mail') btnGroup += '<a class="btlink receiveMail">Recipient</a>&nbsp;|&nbsp;';
											btnGroup +=
												'<a class="btlink configEdit">' +
												lan.public.edit +
												'</a>&nbsp;|&nbsp;<a class="btlink alertTest">Test</a>&nbsp;|&nbsp;<a class="btlink uninstall_alert">' +
												lan.public.del +
												'</a>';
											if (item.name == 'wx_account')
												btnGroup = '<a class="btlink replaceWx">Bind</a>&nbsp;|&nbsp;<a class="btlink alertTest">Test</a>&nbsp;|&nbsp;<a class="btlink uninstall_alert">' + lan.public.del + '</a>';
										} else {
											btnGroup = '<a class="btlink configEdit">' + lan.public.set + '</a>';
										}
									} else {
										btnGroup = '<a class="btlink uninstall_alert">' + lan.public.del + '</a>';
									}
								} else {
									btnGroup = '<a class="btlink configEdit">' + lan.public.set + '</a>';
								}
								var renderHTML = '<tr data-name="'
									.concat(item.name, '">\n\t\t\t\t<td style="font-size: 0;">\n\t\t\t\t\t<i class="config-alert-icon alert-icon-')
									.concat(item.name, '"></i>\n\t\t\t\t\t<div class="alert-config-content">\n\t\t\t\t\t\t<span style="cursor:pointer" class="')
									.concat(item.name === 'wx_account' ? (item.setup ? 'replaceWx' : 'configEdit') : item.name === 'sms' ? '' : 'configEdit', '">')
									.concat(item.title, '</span>\n\t\t\t\t\t\t<p>')
									.concat(item.ps, '<a class="btlink" target="_blank" href="')
									.concat(item.help, '">>>')
									.concat(lan.public.help, '</a></p>\n\t\t\t\t\t</div>\n\t\t\t\t</td>\n\t\t\t\t<td>')
									.concat(_this.renderAlertModelConfigInfo(item), '</td>\n\t\t\t\t<td>')
									.concat(item.version, '</td>\n\t\t\t\t<td style="text-align: right;">')
									.concat(btnGroup, '</td>\n\t\t\t</tr>');
								item.name === 'wx_account' ? (prevHTML = renderHTML) : (tbody += renderHTML);
							});
							html =
								'<div class="divtable">\n\t\t\t\t\t\t\t<table class="table table-hover" id="panel_menu_tab">\n\t\t\t\t\t\t\t\t<thead>\n\t\t\t\t\t\t\t\t\t<tr><th width="440">Alarm module</th><th>Configuration</th><th width="70">Version</th><th style="text-align: right;">'
									.concat(lan.public.operate, '</th></tr>\n\t\t\t\t\t\t\t\t</thead>\n\t\t\t\t\t\t\t\t<tbody>')
									.concat(prevHTML + tbody, '</tbody>\n\t\t\t\t\t\t\t</table>\n\t\t\t\t\t\t</div>');
							$('#alertConfig').html(html);
							this.alertEventBind(ChannelInfo);
							return [2];
					}
				});
			});
		};
		Config.prototype.renderAlertModelConfigInfo = function (mode) {
			var _info = '',
				noConfig = '<a class="bterror configEdit">Unconfigured</a>',
				_data = mode.data,
				isEmpty = $.isEmptyObject(_data);
			if (mode.setup) {
				if (mode.name != 'sms' && mode.name != 'wx_account') {
					if (!$.isEmptyObject(_data)) {
						switch (mode.name) {
							case 'mail':
								if (_data.receive[0] == '') {
									_info = '<a class="bterror receiveMail">No incoming email set</a>';
								} else {
									_info = ''.concat(_data.receive.length, ' incoming email has been set up, <a class="btlink receiveMail">Click to view</a>');
								}
								break;
							case 'dingding':
							case 'feishu':
							case 'weixin':
								_info = 'Receiver: ['.concat(isEmpty ? '' : _data.list.default.title, ']');
								break;
							case 'tg':
								_info = 'Receiver: ['.concat(isEmpty ? '' : _data.my_id, ']');
								break;
						}
					} else {
						_info = noConfig;
					}
				} else if (mode.name == 'sms') {
					_info = '\u5269\u4F59\u53D1\u9001\u544A\u8B66'.concat(_data.count, '\u6B21');
				} else if (mode.name == 'wx_account') {
					var boundCheck = '',
						res = $.isEmptyObject(_data) ? { is_subscribe: 0, is_bound: 0 } : _data.res;
					if (!res.is_subscribe || !res.is_bound) boundCheck = '<a class="bterror replaceWx" style="margin-left:0">未订阅公众号或绑定微信</a>';
					if (res.is_subscribe && res.is_bound) boundCheck = '\u5FAE\u4FE1\u8D26\u53F7\u3010'.concat(res.nickname, '\u3011,\u4ECA\u65E5\u5269\u4F59\u53D1\u9001\u6B21\u6570:').concat(res.remaining);
					_info = boundCheck;
				}
			} else {
				_info = noConfig;
			}
			return _info;
		};
		Config.prototype.alertEventBind = function (info) {
			var _this = this;
			$('.receiveMail').click(function () {
				return __awaiter(_this, void 0, void 0, function () {
					var currentItem;
					var _this = this;
					return __generator(this, function (_a) {
						switch (_a.label) {
							case 0:
								return [4, this.$request('getMessageChannel', { loading: false, msg: false })];
							case 1:
								currentItem = _a.sent();
								this.$open({
									title: 'Recipient Email',
									area: ['335px', '280px'],
									btn: [lan.public.save, lan.public.cancel],
									skin: 'alert-receive-view',
									content:
										'<div class="pd15"><textarea name="recipient_textarea" class="bt-input-text mr5" type="text" style="width: 300px; height:150px; line-height:20px"></textarea>\n\t\t\t\t<div class="placeholder c9 reci_tips" style="position: absolute;top: 25px;left: 25px; display:none">Fill in one mailbox per line, e: <br>xxx@163.com<br>xxx@qq.com</div></div>',
									success: function () {
										var _tips = $('textarea[name=recipient_textarea]');
										var msg = '';
										if (!$.isEmptyObject(currentItem['mail']['data']['receive'])) {
											msg = currentItem['mail']['data']['receive'] ? currentItem['mail']['data']['receive'].join('\n') : '';
										}
										_tips.html(msg);
										if (_tips.val() == '') $('.reci_tips.placeholder').show();
										$('.placeholder').click(function () {
											$(this).hide().siblings('textarea').focus();
										});
										_tips.focus(function () {
											$('.reci_tips.placeholder').hide();
										});
										_tips.blur(function () {
											_tips.val() == '' ? $('.reci_tips.placeholder').show() : $('.reci_tips.placeholder').hide();
										});
									},
									yes: function (config) {
										return __awaiter(_this, void 0, void 0, function () {
											var close, reci_, rdata;
											return __generator(this, function (_a) {
												switch (_a.label) {
													case 0:
														close = config.close;
														reci_ = $('textarea[name=recipient_textarea]').val();
														return [4, this.$request('setMsgConfigmail', { mails: reci_ })];
													case 1:
														rdata = _a.sent();
														rdata.status && close();
														return [2];
												}
											});
										});
									},
								});
								return [2];
						}
					});
				});
			});
			$('.configEdit').click(function (ev) {
				return __awaiter(_this, void 0, void 0, function () {
					var _type;
					return __generator(this, function (_a) {
						_type = $(ev.currentTarget).parents('tr').data('name');
						this.setAlertConfigType(_type);
						return [2];
					});
				});
			});
			$('.alertTest').click(function (ev) {
				return __awaiter(_this, void 0, void 0, function () {
					var _type;
					return __generator(this, function (_a) {
						switch (_a.label) {
							case 0:
								_type = $(ev.currentTarget).parents('tr').data('name');
								return [4, this.$request(['config/get_msg_fun', 'Testing Send, Please wait...'], { fun_name: 'push_data', module_name: _type, msg: 'Testing Send' })];
							case 1:
								_a.sent();
								return [2];
						}
					});
				});
			});
			$('.replaceWx').click(function () {
				_this.setAlertConfigType('wx_account');
			});
			$('.uninstall_alert').click(function (ev) {
				return __awaiter(_this, void 0, void 0, function () {
					var _type, rdata, _a;
					return __generator(this, function (_b) {
						switch (_b.label) {
							case 0:
								_type = $(ev.currentTarget).parents('tr').data('name');
								return [
									4,
									this.$confirm({
										title: 'Delete ' + info[_type].title + ' module',
										msg: 'After deleting the ' + info[_type].title + ' module, it will not be able to send panel alert messages, should I continue?',
									}),
								];
							case 1:
								_b.sent();
								return [4, this.$request(['config/uninstall_msg_module&name=' + _type, 'Delete ' + info[_type].title + ' alert module'])];
							case 2:
								rdata = _b.sent();
								_a = rdata.status;
								if (!_a) return [3, 4];
								return [4, this.alertConfigTable()];
							case 3:
								_a = _b.sent();
								_b.label = 4;
							case 4:
								_a;
								return [2];
						}
					});
				});
			});
		};
		Config.prototype.alertLogsTable = function () {
			return __awaiter(this, void 0, void 0, function () {
				return __generator(this, function (_a) {
					$('#alertLog').empty();
					bt_tools.table({
						el: '#alertLog',
						load: 'Getting the alarm log list',
						url: '/push?action=get_push_logs',
						default: 'The alarm log is empty',
						dataFilter: function (res) {
							return { data: res.data };
						},
						column: [
							{
								fid: 'log',
								title: 'Title',
								type: 'text',
							},
							{
								fid: 'addtime',
								title: 'Time',
								type: 'text',
							},
						],
						tootls: [
							{
								type: 'page',
								positon: ['right', 'bottom'],
								pageParam: 'p',
								page: 1,
								numberParam: 'limit',
								number: 20,
								numberList: [10, 20, 50, 100, 200],
								numberStatus: true,
								jump: true,
							},
						],
					});
					return [2];
				});
			});
		};
		return Config;
	})(public_1.default);
	exports.Config = Config;
});
