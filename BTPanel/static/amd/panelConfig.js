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
var __importDefault =
	(this && this.__importDefault) ||
	function (mod) {
		return mod && mod.__esModule ? mod : { default: mod };
	};
define(['require', 'exports', './snabbdom', './configMixin'], function (require, exports, snabbdom_1, configMixin_1) {
	'use strict';
	Object.defineProperty(exports, '__esModule', { value: true });
	configMixin_1 = __importDefault(configMixin_1);
	var PanelConfig = (function (_super) {
		__extends(PanelConfig, _super);
		function PanelConfig() {
			var _this = _super.call(this) || this;
			_this.apiInfo = {
				closePanel: ['config/ClosePanel', lan.public.the],
				setIpv6Status: ['config/set_ipv6_status', lan.config.setting_up],
				setLocal: ['config/set_local', lan.public.the],
				setDebug: ['config/set_debug', lan.public.the],
				getToken: ['config/get_token', lan.config.get_api],
				setToken: ['config/set_token', lan.config.is_submitting],
				setUserName: ['config/setUsername', lan.public.the],
				setPassword: ['config/setPassword', lan.public.the],
				setLanguage: ['config/set_language', lan.public.the],
				downloadLanguage: ['config/download_language', lan.public.the],
				uploadLanguage: ['config/upload_language', lan.public.the],
				getMenuList: ['config/get_menu_list', 'Getting panel menu bar, please wait...'],
				setHideMenuList: ['config/set_hide_menu_list', 'Setting panel menu bar display status, please wait...'],
			};
			_this.$apiInit(_this.apiInfo);
			return _this;
		}
		PanelConfig.prototype.init = function (data) {
			var configInfo = data.configInfo,
				menuList = data.menuList,
				bindUserInfo = data.bindUserInfo;
			var ipv6 = configInfo.ipv6,
				is_local = configInfo.is_local,
				debug = configInfo.debug,
				api = configInfo.api,
				session_timeout = configInfo.session_timeout,
				sites_path = configInfo.sites_path,
				backup_path = configInfo.backup_path,
				panel = configInfo.panel,
				systemdate = configInfo.systemdate;
			var address = (panel || {}).address;
			var bindUserStatus = bindUserInfo.status,
				bindUsername = bindUserInfo.data.username;
			var username = sessionInfo.username,
				webname = sessionInfo.title;
			var hideMenuList = [];
			menuList.forEach(function (item) {
				return !item.show && hideMenuList.push(item.title);
			});
			var hideMenuValue = hideMenuList.length > 0 ? hideMenuList.join(', ') : 'No hidden bar';
			var formColumns = {
				ipv6: { value: ipv6 === 'checked' },
				is_local: { value: is_local === 'checked' },
				debug: { value: debug === 'checked' },
				api: { value: api === 'checked' },
				webname: { value: webname },
				session_timeout: { value: session_timeout },
				sites_path: { value: sites_path },
				backup_path: { value: backup_path },
				address: { value: address },
				systemdate: { value: systemdate },
				username: { value: username },
				password: { value: '********' },
				bind_user_info: { value: bindUsername },
				menu_hide_list: { value: hideMenuValue },
			};
			this.renderFormColumn(formColumns);
			$('.seconds').text(session_timeout || 0);
			this.bindUsername = bindUserStatus ? bindUsername : '';

			var selectHtml = '';
			$.each(configInfo.language_list, function (index, item) {
				selectHtml += `<option value="${item.name}">${item.title}</option>`;
			});
			$('select[name="language"]').html(selectHtml);
			$('select[name="language"]').val(configInfo.language);
		};
		PanelConfig.prototype.event = function () {
			var _this = this;
			$('input[name="close_panel"]').change(function (e) {
				var title = lan.config.close_panel_title;
				var msg = lan.config.close_panel_msg;
				var api = 'closePanel';
				_this
					.showCheckboxConfirm({
						e: e,
						api: api,
						config: { title: title, msg: msg },
					})
					.then(function (res) {
						_this.$refreshBrowser();
					})
					.catch(function (err) {});
			});
			$('input[name="ipv6"]').change(function (e) {
				_this.changeCheckbox(e, 'setIpv6Status').catch(function (err) {});
			});
			$('input[name="is_local"]').change(function (e) {
				var checked = $(e.target).prop('checked');
				var title = ''.concat(checked ? 'Open' : 'Close', ' developer mode');
				var msg = 'Do you confirm to '.concat(checked ? 'open' : 'close', ' developer mode?');
				var api = 'setLocal';
				_this.showCheckboxConfirm({ e: e, api: api, config: { title: title, msg: msg } }).catch(function (err) {});
			});
			$('input[name="debug"]').change(function (e) {
				var checked = $(e.target).prop('checked');
				if (checked) {
					_this.setDeveloperView(e);
				} else {
					var title = 'Close developer mode';
					var msg = 'Do you confirm to close developer mode?';
					var api = 'setDebug';
					_this
						.showCheckboxConfirm({
							e: e,
							api: api,
							config: { title: title, msg: msg },
						})
						.catch(function (err) {});
				}
			});
			$('input[name="api"]').change(function (e) {
				var checked = $(e.target).prop('checked');
				if (checked) {
					_this.setPanelApiView(checked);
					_this.$request('setToken', { t_type: 1 });
				} else {
					_this.changeCheckbox(e, 'setToken', { t_type: 2 }).catch(function (err) {});
				}
			});
			$('.sitesPath').on('click', function () {
				return _this.selectFileDir('input[name="sites_path"]', 'dir', function () {});
			});
			$('.backupPath').on('click', function () {
				return _this.selectFileDir('input[name="backup_path"]', 'dir', function () {});
			});
			$('.apiInterfaceBtn').click(function () {
				return _this.setPanelApiView();
			});
			$('.editPanelAccount').click(function () {
				return _this.setPanelUserView();
			});
			$('.editPanelPassword').click(function () {
				return _this.setPanelPawView();
			});
			$('.bindBtUser').click(function () {
				return _this.bindBtAccount(!!_this.bindUsername);
			});
			$('.unbindBtUser').click(function () {
				return _this.unbindUser();
			});
			$('.menuBarManage').click(function () {
				return _this.setPanelGroundView();
			});

			$('select[name="language"]').change(function () {
				var $select = $(this);
				var lang = $select.val();
				_this.$request('setLanguage', { name: lang }).then(function (res) {
					if (res.status) {
						_this.$refreshBrowser(3000);
					}
				});
			});

			// 上传语言包弹框
			$('.uploadLanguage').click(function () {
				_this.$open({
					title: 'Upload my translation file',
					area: ['500px', '224px'],
					content: `
					            <div style="padding: 24px;">
					                <ul class="help-info-text explainDescribeList c7 pd15" style="margin-top: 0; margin-bottom: 0;">
					                    <li>Upload my language pack and apply it immediately</li>
					                    <li>Note: The uploaded language pack will be displayed as [Custom]</li>
					                </ul>
					            </div>
					        `,
					btn: ['Upload', lan.public.cancel],
					yes: function () {
						var path = '/www/server/panel/BTPanel/static/upload_language';
						bt_upload_file.open(path, '.gz,.tar,.tar.gz,.zip', 'Upload tar.gz package', function () {
							var filePath = $('#file_input').val();
							var fileName = filePath.split('\\').pop().split('/').pop();
							$('#filesClose').click();
							_this.$request('uploadLanguage', { filename: fileName }).then(function (res) {
								if (res.status) {
									_this.$refreshBrowser(3000);
								}
							});
						});
					},
				});
			});

			// 下载语言包弹框
			$('.downloadLanguage').click(function () {
				_this.$open({
					title: false,
					area: ['520px', '240px'],
					content: `
					            <div style="padding-top: 40px;">
					                <div style="margin-bottom: 20px; text-align: center; font-size: 14px;">You will download a language pack template that you can translate:</div>
					                <div style="margin-bottom: 40px; text-align: center;">
    					                <button type="button" class="btn btn-success btn-sm download-btn">
    								        Download template
    							        </button>
							        </div>
							        <div style="text-align: center; font-size: 14px;">
							            <div style="margin-bottom: 8px;">Translation Tools: </div>
							            <div>
							                <a class="btlink" href="https://translate.google.com/" target="_blank">Google Translate</a>
							            </div>
							        </div>
					            </div>
					        `,
					success: function () {
						$('.download-btn').click(function () {
							_this.$request('downloadLanguage').then(function (res) {
								if (res.path) {
									window.open(`/download?filename=${res.path}`);
								}
							});
						});
					},
				});
			});
		};
		PanelConfig.prototype.setDeveloperView = function (event) {
			var _this = this;
			this.$open({
				title: 'Turn on developer mode',
				area: ['460px', '340px'],
				btn: [lan.public.submit, lan.public.cancel],
				content: {
					data: { agreement: false },
					template: function () {
						return (0, snabbdom_1.jsx)(
							'div',
							{ class: this.$class('bt-form pd25') },
							this.$warningTitle('Risk ordinary users do not open!'),
							this.$ul({ className: 'explainDescribeList pd15' }, [
								['For development use only;', 'red'],
								['Please do not enable it in production environment;'],
								['It may take up a lot of memory after opening;'],
							]),
							this.$learnMore({ title: 'I understand and am willing to take the risk, confirm to open', model: 'agreement', id: 'checkDevelopers' })
						);
					},
				},
				yes: function (config) {
					return __awaiter(_this, void 0, void 0, function () {
						var close, vm, status;
						return __generator(this, function (_a) {
							switch (_a.label) {
								case 0:
									(close = config.close), (vm = config.vm);
									if (!vm.agreement) return [2, this.$tips({ msg: 'Please tick to understand the risk options', el: '#checkDevelopers' })];
									return [4, this.$request('setDebug')];
								case 1:
									status = _a.sent().status;
									if (status) {
										close();
										this.$refreshBrowser();
									}
									return [2];
							}
						});
					});
				},
				cancel: function () {
					_this.changeReverseCheckbox(event);
				},
				btn2: function () {
					_this.changeReverseCheckbox(event);
				},
			}).catch(function (err) {});
		};
		PanelConfig.prototype.setPanelApiView = function (checked) {
			return __awaiter(this, void 0, void 0, function () {
				var that, $checked, rdata, error_1;
				var _this = this;
				return __generator(this, function (_a) {
					switch (_a.label) {
						case 0:
							that = this;
							$checked = $('input[name="api"]');
							return [4, this.$request('getToken')];
						case 1:
							rdata = _a.sent();
							_a.label = 2;
						case 2:
							_a.trys.push([2, 4, , 5]);
							return [
								4,
								this.$open({
									area: '522px',
									title: lan.config.set_api,
									content: {
										data: {
											api: typeof checked === 'undefined' ? rdata.open : checked,
											panelTokenValue: rdata.token,
											apiLimitAddr: rdata.limit_addr,
										},
										template: function () {
											var lineWidth = '125px',
												helpHref = 'https://www.aapanel.com/forum/d/482-api-interface-tutorial';
											return (0, snabbdom_1.jsx)(
												'div',
												{ class: this.$class('bt-form'), style: this.$style('padding: 15px 25px;') },
												this.$line({ title: lan.config.api, width: lineWidth }, this.$switch({ model: 'api', change: this.setPanelApi.bind(this) })),
												this.$line(
													{ title: lan.config.int_sk, width: lineWidth },
													this.$box(
														this.$input({ model: 'panelTokenValue', disabled: true, style: { width: '310px' } }),
														this.$button({ size: 'xs', click: this.resetInterface.bind(this), style: 'margin-left: -56px;', title: lan.config.reset })
													)
												),
												this.$line(
													{
														title: (0, snabbdom_1.jsx)('span', null, lan.config.ip_white_list, (0, snabbdom_1.jsx)('br', null), '(', lan.config.one_per_line, ')'),
														width: lineWidth,
														style: 'overflow: initial;height:20px;line-height:20px;',
													},
													this.$textarea({ model: 'apiLimitAddr', style: 'width: 310px;height:80px;line-height: 20px;padding: 5px 8px;' })
												),
												this.$line({ title: '', width: lineWidth }, this.$button({ size: 'sm', click: this.savePanelApiIp.bind(this), title: lan.config.save })),
												this.$ul({ style: { marginLeft: '16px' } }, [
													[lan.config.help1],
													[lan.config.help2],
													[(0, snabbdom_1.jsx)('span', null, lan.config.help3, ': ', this.$link({ title: helpHref, href: helpHref }))],
												])
											);
										},
										methods: {
											setPanelApi: function () {
												return __awaiter(this, void 0, void 0, function () {
													var res;
													return __generator(this, function (_a) {
														switch (_a.label) {
															case 0:
																return [4, that.$request('setToken', { t_type: 2 })];
															case 1:
																res = _a.sent();
																if (res.status) {
																	$checked.prop('checked', this.api);
																} else {
																	this.api = !this.api;
																}
																return [2];
														}
													});
												});
											},
											resetInterface: function () {
												return __awaiter(this, void 0, void 0, function () {
													var _this = this;
													return __generator(this, function (_a) {
														that
															.$confirm({
																title: 'Reset key',
																msg: 'Are you sure you want to reset your current key?<br><span style="color: red; ">After the key is reset, the associated key product will be invalid. Please re-add the new key to the product.</span>',
															})
															.then(function (res) {
																return that.$request('setToken', { t_type: 1 }, false);
															})
															.then(function (res) {
																if (res.status) {
																	_this.panelTokenValue = res.msg;
																	that.$msg({ msg: lan.config.create_int_key_success, time: 0, closeBtn: 2 });
																} else {
																	throw new Error(res);
																}
															})
															.catch(function (err) {});
														return [2];
													});
												});
											},
											savePanelApiIp: function () {
												return __awaiter(this, void 0, void 0, function () {
													return __generator(this, function (_a) {
														switch (_a.label) {
															case 0:
																return [4, that.$request('setToken', { t_type: 3, limit_addr: this.apiLimitAddr })];
															case 1:
																_a.sent();
																return [2];
														}
													});
												});
											},
										},
									},
									success: function (layers, indexs, vm) {
										return __awaiter(_this, void 0, void 0, function () {
											return __generator(this, function (_a) {
												switch (_a.label) {
													case 0:
														this.setLayerVerticalCenter(layers);
														$('.btswitch-btn').css('margin-bottom', '0');
														if (!(typeof checked === 'boolean' && checked)) return [3, 2];
														return [4, that.$request('setToken', { t_type: 2 })];
													case 1:
														_a.sent();
														_a.label = 2;
													case 2:
														return [2];
												}
											});
										});
									},
								}),
							];
						case 3:
							_a.sent();
							return [3, 5];
						case 4:
							error_1 = _a.sent();
							return [3, 5];
						case 5:
							return [2];
					}
				});
			});
		};
		PanelConfig.prototype.setPanelUserView = function () {
			return __awaiter(this, void 0, void 0, function () {
				var error_2;
				var _this = this;
				return __generator(this, function (_a) {
					switch (_a.label) {
						case 0:
							_a.trys.push([0, 2, , 3]);
							return [
								4,
								this.$open({
									title: lan.bt.user_title,
									area: ['380px', '235px'],
									btn: [lan.public.edit, lan.public.close],
									content: {
										data: { username1: sessionInfo.username, username2: '' },
										template: function () {
											var lineWidth = '110px',
												inputWidth = '210px';
											return (0, snabbdom_1.jsx)(
												'div',
												{ class: this.$class('bt-form pd25') },
												this.$line({ title: lan.bt.user, width: lineWidth }, this.$input({ model: 'username1', width: inputWidth })),
												this.$line({ title: lan.bt.user_new, width: lineWidth }, this.$input({ model: 'username2', width: inputWidth }))
											);
										},
									},
									yes: function (config) {
										return __awaiter(_this, void 0, void 0, function () {
											var close, vm, username1, username2, weakCipher, rdata;
											return __generator(this, function (_a) {
												switch (_a.label) {
													case 0:
														(close = config.close), (vm = config.vm);
														(username1 = vm.username1), (username2 = vm.username2);
														weakCipher = ['admin', 'root', 'admin123', '123456'];
														return [
															4,
															this.$verifySubmitList([
																[username1.length <= 3, lan.bt.user_len],
																[weakCipher.indexOf(username1) > -1, lan.public.usually_username_ban],
																[username1 !== username2, lan.bt.user_err_re],
															]),
														];
													case 1:
														_a.sent();
														username1 = rsa.encrypt_public(encodeURIComponent(username1));
														username2 = rsa.encrypt_public(encodeURIComponent(username2));
														return [4, this.$request('setUserName', { username1: username1, username2: username2 })];
													case 2:
														rdata = _a.sent();
														rdata.status && close() && this.$refreshBrowser('/login?dologin=True');
														return [2];
												}
											});
										});
									},
								}),
							];
						case 1:
							_a.sent();
							return [3, 3];
						case 2:
							error_2 = _a.sent();
							return [3, 3];
						case 3:
							return [2];
					}
				});
			});
		};
		PanelConfig.prototype.setPanelPawView = function () {
			return __awaiter(this, void 0, void 0, function () {
				var that_1, error_3;
				var _this = this;
				return __generator(this, function (_a) {
					switch (_a.label) {
						case 0:
							_a.trys.push([0, 2, , 3]);
							that_1 = this;
							return [
								4,
								this.$open({
									title: lan.bt.pass_title,
									area: ['410px', '235px'],
									btn: [lan.public.edit, lan.public.close],
									content: {
										data: { password1: '', password2: '' },
										template: function () {
											var lineWidth = '110px',
												inputWidth = '210px';
											return (0, snabbdom_1.jsx)(
												'div',
												{ class: { 'bt-form': true, pd25: true } },
												this.$line(
													{ title: lan.public.pass, width: lineWidth },
													this.$box(this.$input({ model: 'password1', width: inputWidth }), this.$icon({ type: 'repeat', click: this.showPaw.bind(this), class: 'ml5' }))
												),
												this.$line({ title: lan.bt.pass_new_title, width: lineWidth }, this.$input({ model: 'password2', width: inputWidth }))
											);
										},
										methods: {
											showPaw: function () {
												this.password1 = that_1.$getRandom(10);
												this.password2 = this.password1;
											},
										},
									},
									yes: function (config) {
										return __awaiter(_this, void 0, void 0, function () {
											var close, vm, password1, password2, weakCipher, rdata;
											return __generator(this, function (_a) {
												switch (_a.label) {
													case 0:
														(close = config.close), (vm = config.vm);
														(password1 = vm.password1), (password2 = vm.password2);
														weakCipher = this.$checkWeakCipher(password1);
														return [
															4,
															this.$verifySubmitList([
																[password1.length < 8, lan.bt.pass_err_len],
																[!weakCipher.status, lan.bt.pass_err + weakCipher.msg],
																[password1 !== password2, lan.bt.pass_err_re],
															]),
														];
													case 1:
														_a.sent();
														password1 = rsa.encrypt_public(encodeURIComponent(password1));
														password2 = rsa.encrypt_public(encodeURIComponent(password2));
														return [4, this.$request('setPassword', { password1: password1, password2: password2 })];
													case 2:
														rdata = _a.sent();
														rdata.status && close() && this.$refreshBrowser('/login?dologin=True');
														return [2];
												}
											});
										});
									},
								}),
							];
						case 1:
							_a.sent();
							return [3, 3];
						case 2:
							error_3 = _a.sent();
							return [3, 3];
						case 3:
							return [2];
					}
				});
			});
		};
		PanelConfig.prototype.unbindUser = function () {
			return __awaiter(this, void 0, void 0, function () {
				var rdata, err_1;
				return __generator(this, function (_a) {
					switch (_a.label) {
						case 0:
							_a.trys.push([0, 3, , 4]);
							return [
								4,
								this.$confirm({
									title: 'Unbind aaPanel account',
									msg: 'Unbind the aaPanel account and continue!',
								}),
							];
						case 1:
							_a.sent();
							return [4, this.$request('unbindUserInfo')];
						case 2:
							rdata = _a.sent();
							if (rdata.status) {
								this.$removeCookie('bt_user_info');
								this.$refreshBrowser();
							}
							return [3, 4];
						case 3:
							err_1 = _a.sent();
							return [3, 4];
						case 4:
							return [2];
					}
				});
			});
		};
		PanelConfig.prototype.setPanelGroundView = function () {
			return __awaiter(this, void 0, void 0, function () {
				var rdata, html, is_option, that, arry, isEdit;
				return __generator(this, function (_a) {
					switch (_a.label) {
						case 0:
							return [4, this.$request('getMenuList')];
						case 1:
							(rdata = _a.sent()), (html = ''), (is_option = ''), (that = this);
							arry = ['dologin', 'memuAconfig', 'memuAsoft', 'memuA'];
							rdata.map(function (item, index) {
								is_option = '<div class="index-item" style="float:right;"><input class="btswitch btswitch-ios" id="'
									.concat(item.id, '-')
									.concat(index, '" name="')
									.concat(item.id, '" type="checkbox" ')
									.concat(item.show ? 'checked' : '', '><label class="btswitch-btn" for="')
									.concat(item.id, '-')
									.concat(index, '"></label></div>');
								arry.indexOf(item.id) > -1 && (is_option = 'Inoperable');
								html += '<tr><td>'.concat(item.title, '</td><td><div style="float:right;">').concat(is_option, '</div></td></tr>');
							});
							isEdit = false;
							return [
								4,
								this.$open({
									title: 'Manage panel menu bar',
									area: ['350px', '598px'],
									content:
										'\n        <div class="divtable softlist" id="panel_menu_tab" style="padding: 20px 15px;">\n          <table class="table table-hover">\n            <thead>\n              <tr>\n                <th>Menu bar</th>\n                <th class="text-right" style="width:120px;">Display</th>\n              </tr>\n            </thead>\n            <tbody>'.concat(
											html,
											'</tbody>\n          </table>\n        </div>\n      '
										),
									success: function () {
										$('#panel_menu_tab input').click(function () {
											return __awaiter(this, void 0, void 0, function () {
												var arry;
												return __generator(this, function (_a) {
													switch (_a.label) {
														case 0:
															arry = [];
															$(this)
																.parents('tr')
																.siblings()
																.each(function (index, el) {
																	if ($(this).find('input').length > 0 && !$(this).find('input').prop('checked')) {
																		arry.push($(this).find('input').attr('name'));
																	}
																});
															!$(this).prop('checked') && arry.push($(this).attr('name'));
															return [4, that.$request('setHideMenuList', { hide_list: JSON.stringify(arry) })];
														case 1:
															_a.sent();
															isEdit = true;
															return [2];
													}
												});
											});
										});
									},
									cancel: function () {
										isEdit && that.$refreshBrowser(0);
									},
								}),
							];
						case 2:
							_a.sent();
							return [2];
					}
				});
			});
		};
		return PanelConfig;
	})(configMixin_1.default);
	exports.default = PanelConfig;
});
