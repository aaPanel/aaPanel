var __extends = (this && this.__extends) || (function () {
	var extendStatics = function (d, b) {
			extendStatics = Object.setPrototypeOf ||
					({ __proto__: [] } instanceof Array && function (d, b) { d.__proto__ = b; }) ||
					function (d, b) { for (var p in b) if (Object.prototype.hasOwnProperty.call(b, p)) d[p] = b[p]; };
			return extendStatics(d, b);
	};
	return function (d, b) {
			if (typeof b !== "function" && b !== null)
					throw new TypeError("Class extends value " + String(b) + " is not a constructor or null");
			extendStatics(d, b);
			function __() { this.constructor = d; }
			d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
	};
})();
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
	function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
	return new (P || (P = Promise))(function (resolve, reject) {
			function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
			function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
			function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
			step((generator = generator.apply(thisArg, _arguments || [])).next());
	});
};
var __generator = (this && this.__generator) || function (thisArg, body) {
	var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g;
	return g = { next: verb(0), "throw": verb(1), "return": verb(2) }, typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
	function verb(n) { return function (v) { return step([n, v]); }; }
	function step(op) {
			if (f) throw new TypeError("Generator is already executing.");
			while (_) try {
					if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
					if (y = 0, t) op = [op[0] & 2, t.value];
					switch (op[0]) {
							case 0: case 1: t = op; break;
							case 4: _.label++; return { value: op[1], done: false };
							case 5: _.label++; y = op[1]; op = [0]; continue;
							case 7: op = _.ops.pop(); _.trys.pop(); continue;
							default:
									if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
									if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
									if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
									if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
									if (t[2]) _.ops.pop();
									_.trys.pop(); continue;
					}
					op = body.call(thisArg, _);
			} catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
			if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
	}
};
var __importDefault = (this && this.__importDefault) || function (mod) {
	return (mod && mod.__esModule) ? mod : { "default": mod };
};
define(["require", "exports", "./snabbdom", "./configMixin"], function (require, exports, snabbdom_1, configMixin_1) {
	"use strict";
	Object.defineProperty(exports, "__esModule", { value: true });
	configMixin_1 = __importDefault(configMixin_1);
	var SafeConfig = (function (_super) {
			__extends(SafeConfig, _super);
			function SafeConfig() {
					var _this = _super.call(this) || this;
					_this.apiInfo = {
							getCertSource: ['config/get_cert_source', lan.public.the],
							setPanelSsl: ['config/SetPanelSSL', lan.public.the],
							getPanelSsl: ['config/GetPanelSSL', lan.config.get_cert],
							savePanelSsl: ['config/SavePanelSSL', lan.config.ssl_msg],
							setBasicAuth: ['config/set_basic_auth', lan.config.set_basicauth],
							setTwoStepAuth: ['config/set_two_step_auth', lan.public.the],
							getQrcodeData: ['config/get_qrcode_data', lan.public.the],
							getTwoStepKey: ['config/get_key', lan.public.the],
							setPasswordSafe: ['config/set_password_safe', lan.public.the],
							setAdminPath: ['config/set_admin_path', lan.config.config_save],
							setNotAuthStatus: ['config/set_not_auth_status', lan.config.panel_entrance_err],
							setPawExpire: ['config/set_password_expire', 'Setting password expiration time, please wait...'],
							getPasswordConfig: ['config/get_password_config', 'Setting password complexity verification status, please wait...'],
							getTempAuthList: ['config/get_temp_login', 'Getting temporary authorization list, please wait...'],
							setTempAuthLink: ['config/set_temp_login', 'Setting temporary links, please wait...'],
							removeTempAuthLink: ['config/remove_temp_login', 'Deleting temporary authorization record, please wait...'],
							clearTempAuth: ['config/clear_temp_login', 'Forcing user to log out, please wait...'],
							getTempOperationLogs: ['config/get_temp_login_logs', 'Getting operation log, please wait...'],
					};
					_this.statusCodeList = [
							{ label: 'security entry error', value: 0 },
							{ label: '403', value: 403 },
							{ label: '404', value: 404 },
							{ label: '416', value: 416 },
							{ label: '408', value: 408 },
							{ label: '400', value: 400 },
							{ label: '401', value: 401 },
					];
					_this.$apiInit(_this.apiInfo);
					return _this;
			}
			SafeConfig.prototype.init = function (data) {
					var configInfo = data.configInfo, twoStep = data.twoStep, pawComplexity = data.pawComplexity;
					var basic_auth = configInfo.basic_auth, panel = configInfo.panel;
					var open = (basic_auth || {}).open;
					var _a = panel || {}, port = _a.port, admin_path = _a.admin_path, domain = _a.domain, limitip = _a.limitip;
					var googleStatus = twoStep.status;
					var password_safe = pawComplexity.password_safe, expire = pawComplexity.expire, expire_time = pawComplexity.expire_time, expire_day = pawComplexity.expire_day;
					var isHttps = location.protocol.indexOf('https:') > -1;
					var statusCodeTips = this.getStatusCodeTips();
					var paw_expire_time = expire > 0 ? "".concat(this.$formatTime(expire_time), " (Exp in ").concat(expire_day, " days)") : lan.config.not_set;
					var formColumns = {
							ssl: { value: isHttps },
							basic_auth: { value: open },
							check_two_step: { value: googleStatus },
							paw_complexity: { value: password_safe },
							port: { value: port },
							admin_path: { value: admin_path },
							status_code: { value: statusCodeTips },
							domain: { value: domain },
							limitip: { value: limitip },
							paw_expire_time: { value: paw_expire_time, day: expire_day },
					};
					this.renderFormColumn(formColumns);
					this.formColumns = formColumns;
			};
			SafeConfig.prototype.event = function () {
					var _this = this;
					$('input[name="ssl"]').change(function (e) {
							var checked = $(e.target).prop('checked');
							if (checked) {
									_this.setPanelSslView(e);
							}
							else {
									var title = 'Tips';
									var msg = 'Whether to close the panel SSL certificate?';
									var api = 'setPanelSsl';
									_this.showCheckboxConfirm({
											e: e,
											api: api,
											config: { title: title, msg: msg },
									})
											.then(function (res) {
											if (res.status)
													return _this.$request('restartPanel', { loading: false, msg: false });
									})
											.then(function (res) {
											res.status && _this.$refreshBrowser(location.href.replace(/^https:/, 'http:'), 800);
									})
											.catch(function (err) { });
							}
					});
					$('.panelSslConfig').on('click', function () { return _this.setPanelSslConfigView(); });
					$('input[name="basic_auth"]').change(function (e) {
							var checked = $(e.target).prop('checked');
							if (checked) {
									_this.setBasicAuthView(e);
							}
							else {
									var title = 'Turn off BasicAuth authentication';
									var msg = 'After BasicAuth authentication is disabled, panel login will no longer verify BasicAuth base authentication, which will cause panel security to decline. Do you want to continue?';
									var api = 'setBasicAuth';
									_this.showCheckboxConfirm({
											e: e,
											api: api,
											config: { title: title, msg: msg },
											data: { open: 'False', basic_user: '', basic_pwd: '' },
									})
											.then(function (res) {
											_this.$refreshBrowser();
									})
											.catch(function (err) { });
							}
					});
					$('input[name="check_two_step"]').change(function (e) {
							var checked = $(e.target).prop('checked');
							if (checked) {
									_this.setGoogleAuthView(e);
							}
							else {
									var title = 'Google authentication';
									var msg = 'Turn off Google authentication, do you want to continue?';
									var api = 'setTwoStepAuth';
									_this.showCheckboxConfirm({
											e: e,
											api: api,
											config: { title: title, msg: msg },
											data: { act: false },
									}).catch(function (err) { });
							}
					});
					$('.checkTwoStepConfig').click(function () { return _this.googleAuthRelationView(); });
					$('input[name="paw_complexity"]').change(function (e) {
							var checked = $(e.target).is(':checked');
							var title = checked ? lan.config.open_strong_password : lan.config.close_strong_password;
							var msg = checked ? "".concat(lan.config.strong_password_desc1, "<span style=\"color:red;\">").concat(lan.config.strong_password_desc2, "</span>") : lan.config.strong_password_desc3;
							var api = 'setPasswordSafe';
							_this.showCheckboxConfirm({
									e: e,
									api: api,
									config: { title: title, msg: msg },
							})
									.then(function (res) {
									res.status && _this.$refreshBrowser();
							})
									.catch(function (err) { });
					});
					$('.setSafetyEntrance').click(function () { return _this.setSafetyEntranceView(); });
					$('.setStatusCodeView').click(function () { return _this.setStatusCodeView(); });
					$('.setPawExpiration').click(function () { return _this.setPawExpirationView(); });
					$('.setTempAuthView').on('click', function () { return _this.setTempAuthView(); });
			};
			SafeConfig.prototype.getStatusCodeTips = function () {
					var statusCodeTips = lan.config.response_msg1;
					var statusCode = sessionInfo.statusCode;
					var code = parseInt(statusCode);
					for (var i = 0; i < this.statusCodeList.length; i++) {
							var item = this.statusCodeList[i];
							if (item.value === code) {
									statusCodeTips = item.label;
									break;
							}
					}
					return statusCodeTips;
			};
			SafeConfig.prototype.setPanelSslView = function (e) {
					return __awaiter(this, void 0, void 0, function () {
							var certSource, _a, certPem, privateKey, err_1;
							var _this = this;
							return __generator(this, function (_b) {
									switch (_b.label) {
											case 0:
													_b.trys.push([0, 4, , 5]);
													return [4, this.$request('getCertSource')];
											case 1:
													certSource = _b.sent();
													return [4, this.$request('getPanelSsl')];
											case 2:
													_a = _b.sent(), certPem = _a.certPem, privateKey = _a.privateKey;
													return [4, this.$open({
																	title: 'Panel SSL',
																	area: '560px',
																	btn: ['Submit', 'Close'],
																	skin: 'panel-ssl',
																	content: {
																			data: { cert_type: certSource.cert_type ? parseInt(certSource.cert_type) : 1, email: certSource.email || '', certPem: certPem, privateKey: privateKey, agreement: false },
																			template: function () {
																					var lineWidth = '80px', inputWidth = '280px', helpHref = 'https://www.aapanel.com/forum/d/167-common-problems-after-opening-the-panel-certificate';
																					return ((0, snabbdom_1.jsx)("div", { class: this.$class('bt-form'), style: this.$style('padding: 20px 50px;') },
																							this.$warningTitle(lan.config.ssl_open_ps),
																							this.$ul({ className: 'explainDescribeList pd15' }, [
																									[lan.config.ssl_open_ps_1, 'red'],
																									[lan.config.ssl_open_ps_2],
																									[(0, snabbdom_1.jsx)("span", null,
																													"If panel is not accessible, you can click the ",
																													this.$link({ title: 'link', href: helpHref }),
																													" below to find solutions")],
																							]),
																							(0, snabbdom_1.jsx)("div", { class: { pt10: true } },
																									this.$line({ title: 'Cert Type', width: lineWidth }, this.$select({
																											model: 'cert_type',
																											width: inputWidth,
																											options: [
																													{ label: 'Self-signed certificate', value: 1 },
																													{ label: "Let's Encrypt", value: 2 },
																													{ label: 'I have certficate', value: 3 },
																											],
																									})),
																									this.$line({ title: 'E-Mail', width: lineWidth, hide: parseInt(this.cert_type) !== 2 }, this.$input({ model: 'email', width: inputWidth, placeholder: 'Admin E-Mail' })),
																									this.$line({ title: 'Key', width: lineWidth, hide: parseInt(this.cert_type) !== 3 }, this.$textarea({ model: 'privateKey', width: inputWidth, height: '100px', style: 'line-height: 16px;padding: 5px 8px;' })),
																									this.$line({ title: 'Certificate', width: lineWidth, hide: parseInt(this.cert_type) !== 3 }, this.$textarea({ model: 'certPem', width: inputWidth, height: '100px', style: 'line-height: 16px;padding: 5px 8px;' })),
																									this.$learnMore({
																											model: 'agreement',
																											id: 'checkSSL',
																											title: (0, snabbdom_1.jsx)("span", null, lan.config.ssl_open_ps_4),
																											link: this.$link({ title: lan.config.ssl_open_ps_5, href: 'https://www.aapanel.com/forum/d/167-common-problems-after-opening-the-panel-certificate' }),
																									}))));
																			},
																	},
																	success: function (layers) {
																			layers[0].style.height = 'auto';
																			layers[0].querySelector('.layui-layer-content').style.height = 'auto';
																			_this.setLayerVerticalCenter(layers);
																			$('select[name="cert_type"]').change(function (e) {
																					_this.setLayerVerticalCenter(layers);
																			});
																	},
																	yes: function (config) { return __awaiter(_this, void 0, void 0, function () {
																			var close, vm, cert_type, email, privateKey, certPem, agreement, _a, res, rdata;
																			return __generator(this, function (_b) {
																					switch (_b.label) {
																							case 0:
																									close = config.close, vm = config.vm;
																									cert_type = vm.cert_type, email = vm.email, privateKey = vm.privateKey, certPem = vm.certPem, agreement = vm.agreement;
																									if (!agreement)
																											return [2, this.$tips({ el: '#agreement_more', msg: 'Please confirm the risk first!' })];
																									return [4, this.$verifySubmitList([
																													[cert_type === '3' && (!certPem || !privateKey), 'Please enter certificate information'],
																													[cert_type === '2' && !email, 'Please enter administrator email'],
																											])];
																							case 1:
																									_b.sent();
																									_a = cert_type === '3';
																									if (!_a) return [3, 3];
																									return [4, this.$request('savePanelSsl', { privateKey: privateKey, certPem: certPem }, false)];
																							case 2:
																									_a = (_b.sent());
																									_b.label = 3;
																							case 3:
																									_a;
																									return [4, this.$request('setPanelSsl', Object.assign({ cert_type: cert_type }, vm.cert_type === '2' ? { email: email } : {}))];
																							case 4:
																									res = _b.sent();
																									if (!res.status) return [3, 6];
																									return [4, this.$request('restartPanel', { loading: false, msg: false })];
																							case 5:
																									rdata = _b.sent();
																									rdata.status && close() && this.$refreshBrowser(location.href.replace(/^http:/, 'https:'), 800);
																									_b.label = 6;
																							case 6: return [2];
																					}
																			});
																	}); },
																	cancel: function () {
																			_this.changeReverseCheckbox(e);
																	},
																	btn2: function () {
																			_this.changeReverseCheckbox(e);
																	},
															})];
											case 3:
													_b.sent();
													return [3, 5];
											case 4:
													err_1 = _b.sent();
													return [3, 5];
											case 5: return [2];
									}
							});
					});
			};
			SafeConfig.prototype.setPanelSslConfigView = function () {
					return __awaiter(this, void 0, void 0, function () {
							var that_1, _a, certPem, privateKey, error_1;
							var _this = this;
							return __generator(this, function (_b) {
									switch (_b.label) {
											case 0:
													_b.trys.push([0, 3, , 4]);
													that_1 = this;
													return [4, this.$request('getPanelSsl')];
											case 1:
													_a = _b.sent(), certPem = _a.certPem, privateKey = _a.privateKey;
													return [4, this.$open({
																	title: lan.config.custom_panel_cert,
																	area: '740px',
																	content: {
																			data: { certPem: certPem, privateKey: privateKey },
																			template: function () {
																					return ((0, snabbdom_1.jsx)("div", { class: this.$class('bt-form pd20') },
																							(0, snabbdom_1.jsx)("div", { class: this.$class('myKeyCon') },
																									(0, snabbdom_1.jsx)("div", { class: this.$class('ssl-con-key pull-left mr20'), style: { width: '48%' } },
																											lan.config.key,
																											(0, snabbdom_1.jsx)("br", null),
																											this.$textarea({ model: 'privateKey' })),
																									(0, snabbdom_1.jsx)("div", { class: this.$class('ssl-con-key pull-left'), style: { width: '48%' } },
																											lan.config.pem_cert,
																											(0, snabbdom_1.jsx)("br", null),
																											this.$textarea({ model: 'certPem' })),
																									(0, snabbdom_1.jsx)("div", { class: this.$class('ssl-btn pull-left mtb15'), style: { width: '100%' } }, this.$button({ title: lan.config.save, click: this.savePanelSsl.bind(this) }))),
																							this.$ul({ style: 'clear: both;' }, [
																									[
																											(0, snabbdom_1.jsx)("span", null,
																													lan.config.ps,
																													" ",
																													this.$link({ title: "[".concat(lan.config.help, "]"), href: 'http://www.bt.cn/bbs/thread-704-1-1.html' }),
																													"."),
																									],
																									[lan.config.ps1],
																									[lan.config.ps2],
																							])));
																			},
																			methods: {
																					savePanelSsl: function () {
																							return __awaiter(this, void 0, void 0, function () {
																									var _a, certPem, privateKey;
																									return __generator(this, function (_b) {
																											switch (_b.label) {
																													case 0:
																															_a = this, certPem = _a.certPem, privateKey = _a.privateKey;
																															return [4, that_1.$verifySubmitList([[!certPem || !privateKey, 'Please enter certificate information']])];
																													case 1:
																															_b.sent();
																															return [4, that_1.$request('savePanelSsl', { privateKey: privateKey, certPem: certPem })];
																													case 2:
																															_b.sent();
																															return [2];
																											}
																									});
																							});
																					},
																			},
																	},
																	success: function (layero) {
																			_this.setLayerVerticalCenter(layero);
																	},
															})];
											case 2:
													_b.sent();
													return [3, 4];
											case 3:
													error_1 = _b.sent();
													return [3, 4];
											case 4: return [2];
									}
							});
					});
			};
			SafeConfig.prototype.setBasicAuthView = function (e) {
					var _this = this;
					this.$open({
							title: 'Risk reminder',
							area: '650px',
							btn: ['Submit', 'Close'],
							content: {
									data: { agreement: false },
									template: function () {
											return ((0, snabbdom_1.jsx)("div", { class: this.$class('bt-form pd25') },
													this.$warningTitle('Warning! Do not understand this feature, do not open!'),
													this.$ul({ className: 'explainDescribeList pd15' }, [
															['You must use and understand this feature to decide if you want to open it!', 'red'],
															['After opening, access the panel in any way, you will be asked to enter the BasicAuth username and password first.'],
															['After being turned on, it can effectively prevent the panel from being scanned and found, but it cannot replace the account password of the panel itself.'],
															['Please remember the BasicAuth password, but forget that you will not be able to access the panel.'],
															['If you forget your password, you can disable BasicAuth authentication by using the bt command in SSH.'],
													]),
													this.$learnMore({
															title: (0, snabbdom_1.jsx)("span", null, "I already know the details and are willing to take risks"),
															model: 'agreement',
															id: 'checkBasicAuth',
															link: this.$link({ title: 'What is BasicAuth authentication?', href: 'https://www.bt.cn/bbs/thread-34374-1-1.html' }),
													})));
									},
							},
							success: function (layers) {
									_this.setLayerVerticalCenter(layers);
							},
							yes: function (config) { return __awaiter(_this, void 0, void 0, function () {
									var close, vm;
									return __generator(this, function (_a) {
											close = config.close, vm = config.vm;
											if (!vm.agreement)
													return [2, this.$tips({ el: '#checkBasicAuth', msg: 'Please read and agree to the risk' })];
											close();
											this.setBasicAuthConfigView(e);
											return [2];
									});
							}); },
							cancel: function () {
									_this.changeReverseCheckbox(e);
							},
							btn2: function () {
									_this.changeReverseCheckbox(e);
							},
					}).catch(function (err) { });
			};
			SafeConfig.prototype.setBasicAuthConfigView = function (e) {
					return __awaiter(this, void 0, void 0, function () {
							var that;
							var _this = this;
							return __generator(this, function (_a) {
									that = this;
									this.$open({
											title: 'Configure BasicAuth authentication',
											area: '500px',
											content: {
													data: { open: true, basic_user: '', basic_pwd: '' },
													template: function () {
															var inputWidth = '280px';
															return ((0, snabbdom_1.jsx)("div", { class: this.$class('bt-form pd25') },
																	this.$line({ title: lan.public.server_status }, this.$switch({ model: 'open' })),
																	this.$line({ title: lan.public.username }, this.$input({ model: 'basic_user', placeholder: lan.config.set_username, width: inputWidth })),
																	this.$line({ title: lan.public.pass }, this.$input({ model: 'basic_pwd', placeholder: lan.config.set_passwd, width: inputWidth })),
																	this.$line({ title: '' }, this.$button({ title: lan.public.save, click: this.saveBasicAuth.bind(this) })),
																	this.$ul([[lan.config.basic_auth_tips1, 'red'], [lan.config.basic_auth_tips2], [lan.config.basic_auth_tips3]])));
													},
													methods: {
															saveBasicAuth: function () {
																	return __awaiter(this, void 0, void 0, function () {
																			var _a, basic_user, basic_pwd, open, rdata;
																			return __generator(this, function (_b) {
																					switch (_b.label) {
																							case 0:
																									_a = this, basic_user = _a.basic_user, basic_pwd = _a.basic_pwd, open = _a.open;
																									return [4, that.$request('setBasicAuth', { basic_user: basic_user, basic_pwd: basic_pwd, open: open ? 'True' : 'False' })];
																							case 1:
																									rdata = _b.sent();
																									if (rdata.status) {
																											this.$closeLayer();
																											that.$refreshBrowser();
																									}
																									return [2];
																					}
																			});
																	});
															},
													},
											},
											success: function (layers) {
													_this.setLayerVerticalCenter(layers);
											},
											cancel: function () {
													_this.changeReverseCheckbox(e);
											},
											btn2: function () {
													_this.changeReverseCheckbox(e);
											},
									}).catch(function (err) { });
									return [2];
							});
					});
			};
			SafeConfig.prototype.setGoogleAuthView = function (e) {
					var _this = this;
					this.$open({
							title: 'Google authentication binding',
							area: ['660px', '390px'],
							btn: ['Submit', 'Close'],
							content: {
									data: { agreement: false },
									template: function () {
											return ((0, snabbdom_1.jsx)("div", { class: this.$class('bt-form pd25') },
													this.$warningTitle('Warning! Do not understand this feature, do not open!'),
													this.$ul({ className: 'explainDescribeList pd15' }, [
															['You must use and understand this feature to decide if you want to open it!', 'red'],
															['If it is not possible to verify, enter "bt 24" on the command line to cancel Google authentication.', 'red'],
															['Once the service is turned on, bind it immediately to avoid the panel being inaccessible.'],
															['After opening, the panel will not be accessible. You can click the link below to find out the solution.'],
													]),
													this.$learnMore({
															title: 'I already know the details and are willing to take risks',
															model: 'agreement',
															id: 'checkAuthenticator',
															link: this.$link({ title: 'Learn more', href: 'https://www.aapanel.com/forum/d/357-how-to-use-google-authenticator-in-the-aapanel' }),
													})));
									},
							},
							yes: function (config) { return __awaiter(_this, void 0, void 0, function () {
									var close, vm, rdata, _a;
									return __generator(this, function (_b) {
											switch (_b.label) {
													case 0:
															close = config.close, vm = config.vm;
															if (!vm.agreement)
																	return [2, this.$tips({ el: '#checkAuthenticator', msg: 'Please read and agree to the risk' })];
															return [4, this.$request('setTwoStepAuth', { act: 1 })];
													case 1:
															rdata = _b.sent();
															_a = rdata.status && close();
															if (!_a) return [3, 3];
															return [4, this.googleAuthRelationView()];
													case 2:
															_a = (_b.sent());
															_b.label = 3;
													case 3:
															_a;
															return [2];
											}
									});
							}); },
							cancel: function () {
									e && _this.changeReverseCheckbox(e);
							},
							btn2: function () {
									e && _this.changeReverseCheckbox(e);
							},
					}).catch(function (err) { });
			};
			SafeConfig.prototype.googleAuthRelationView = function () {
					return __awaiter(this, void 0, void 0, function () {
							var that, checked;
							var _this = this;
							return __generator(this, function (_a) {
									that = this;
									checked = $('input[name="check_two_step"]').is(':checked');
									if (!checked)
											return [2, this.$msg({ msg: 'Please turn on Google authentication first.', icon: 0 })];
									this.$open({
											title: 'Google authentication binding',
											area: ['600px', '660px'],
											content: {
													data: {
															username: '--',
															key: '--',
															type: 'Time based',
													},
													template: function () {
															return ((0, snabbdom_1.jsx)("div", { class: this.$class('bt-form'), style: this.$style('padding:20px 35px;') },
																	(0, snabbdom_1.jsx)("div", { class: this.$class('verify_title') }, "Login authentication based on Google Authenticator"),
																	(0, snabbdom_1.jsx)("div", { class: this.$class('verify_item') },
																			(0, snabbdom_1.jsx)("div", { class: this.$class('verify_vice_title') }, "1. Key binding"),
																			(0, snabbdom_1.jsx)("div", { class: this.$class('verify_conter') },
																					(0, snabbdom_1.jsx)("div", { class: this.$class('verify_box') },
																							(0, snabbdom_1.jsx)("div", { class: this.$class('verify_box_line') },
																									"Account: ",
																									(0, snabbdom_1.jsx)("span", null, this.username)),
																							(0, snabbdom_1.jsx)("div", { class: this.$class('verify_box_line') },
																									"Key: ",
																									(0, snabbdom_1.jsx)("span", null, this.key)),
																							(0, snabbdom_1.jsx)("div", { class: this.$class('verify_box_line') },
																									"Type: ",
																									(0, snabbdom_1.jsx)("span", null, this.type))))),
																	(0, snabbdom_1.jsx)("div", { class: this.$class('verify_item') },
																			(0, snabbdom_1.jsx)("div", { class: this.$class('verify_vice_title') }, "2. Scan code binding (Using Google Authenticator APP scan)"),
																			(0, snabbdom_1.jsx)("div", { class: this.$class('verify_conter'), style: this.$style('text-align:center;padding-top:10px;') },
																					(0, snabbdom_1.jsx)("div", { props: { id: 'verify_qrcode' }, key: 'verifyQrcode' }))),
																	this.$ul({ className: 'verify_tips' }, [
																			[
																					(0, snabbdom_1.jsx)("span", null,
																							"Tips: Please use the \"Google Authenticator APP\" binding to support Android, IOS system.",
																							this.$link({ title: 'Use tutorial', href: 'https://www.aapanel.com/forum/d/357-how-to-use-google-authenticator-in-the-aapanel' })),
																			],
																			['Once you have turned on the service, use the Google Authenticator app binding now to avoid having to sign in.', 'red'],
																	])));
													},
													mounted: function () {
															return __awaiter(this, void 0, void 0, function () {
																	var loadT;
																	var _this = this;
																	return __generator(this, function (_a) {
																			loadT = that.$load(lan.public.the);
																			Promise.all([that.$request('getTwoStepKey', false), that.$request('getQrcodeData', { act: 1 }, false), that.$require('jquery.qrcode')])
																					.then(function (resArr) {
																					var keyRes = resArr[0], qrcodeRes = resArr[1];
																					var username = keyRes.username, key = keyRes.key;
																					_this.username = username;
																					_this.key = key;
																					$('#verify_qrcode').qrcode({ render: 'canvas', width: 150, height: 150, text: qrcodeRes });
																			})
																					.catch(function (err) {
																					_this.$error(err.msg || 'Server Error');
																			})
																					.finally(function () {
																					loadT.close();
																			});
																			return [2];
																	});
															});
													},
											},
											success: function (layers) { return __awaiter(_this, void 0, void 0, function () {
													return __generator(this, function (_a) {
															this.setLayerVerticalCenter(layers);
															return [2];
													});
											}); },
									}).catch(function (err) { });
									return [2];
							});
					});
			};
			SafeConfig.prototype.setSafetyEntranceView = function () {
					var _this = this;
					this.$open({
							title: lan.config.change_safe_entry,
							area: ['420px', '180px'],
							btn: [lan.config.submit, lan.config.turn_off],
							content: {
									data: { expire: this.formColumns.admin_path.value },
									template: function () {
											return (0, snabbdom_1.jsx)("div", { class: this.$class('pd20 bt-form') }, this.$line({ title: lan.config.entry_addr }, this.$input({ model: 'expire', width: '240px' })));
									},
							},
							yes: function (content) { return __awaiter(_this, void 0, void 0, function () {
									var close, vm, admin_path, rdata;
									return __generator(this, function (_a) {
											switch (_a.label) {
													case 0:
															close = content.close, vm = content.vm, admin_path = vm.expire;
															return [4, this.$verifySubmit(!admin_path, 'Entrance address cannot be empty')];
													case 1:
															_a.sent();
															return [4, this.$request('setAdminPath', { admin_path: rsa.encrypt_public(admin_path) })];
													case 2:
															rdata = _a.sent();
															if (rdata.status) {
																	close();
																	$('input[name="admin_path"]').val(admin_path);
																	this.formColumns.admin_path.value = admin_path;
															}
															return [2];
											}
									});
							}); },
					}).catch(function (err) { });
			};
			SafeConfig.prototype.setStatusCodeView = function () {
					var _this = this;
					this.$open({
							title: lan.config.panel_entrance_err,
							area: ['420px', '250px'],
							btn: ['Confirm', 'Cancel'],
							content: {
									data: { status_code: parseInt(sessionInfo.statusCode) },
									template: function () {
											return ((0, snabbdom_1.jsx)("div", { class: this.$class('pd20 bt-form') },
													this.$line({ title: lan.config.response, width: '80px' }, this.$select({
															model: 'status_code',
															width: '250px',
															options: [
																	{ label: lan.config.response_msg1, value: 0 },
																	{ label: '403', value: 403 },
																	{ label: '404', value: 404 },
																	{ label: '416', value: 416 },
																	{ label: '408', value: 408 },
																	{ label: '400', value: 400 },
																	{ label: '401', value: 401 },
															],
													})),
													this.$ul([[lan.config.response_desc, 'red']])));
									},
							},
							yes: function (config) { return __awaiter(_this, void 0, void 0, function () {
									var close, vm, rdata;
									return __generator(this, function (_a) {
											switch (_a.label) {
													case 0:
															close = config.close, vm = config.vm;
															return [4, this.$request('setNotAuthStatus', { status_code: vm.status_code })];
													case 1:
															rdata = _a.sent();
															rdata.status && close() && this.$refreshBrowser();
															return [2];
											}
									});
							}); },
					}).catch(function (err) { });
			};
			SafeConfig.prototype.setPawExpirationView = function () {
					var _this = this;
					var day = this.formColumns.paw_expire_time.day || 0;
					this.$open({
							title: lan.config.set_password_expiration_time,
							area: ['350px', '245px'],
							btn: [lan.public.confirm, lan.public.cancel],
							content: {
									data: { expire: day },
									template: function () {
											return ((0, snabbdom_1.jsx)("div", { class: this.$class('pd20 bt-form') },
													this.$line({ title: lan.config.expire_time }, this.$box(this.$input({ model: 'expire', placeholder: '', width: '120px' }), (0, snabbdom_1.jsx)("span", null, "Days"))),
													this.$ul([[lan.config.expire_password_desc1, 'red'], [lan.config.expire_password_desc2]])));
									},
							},
							yes: function (config) { return __awaiter(_this, void 0, void 0, function () {
									var close, vm, expire, rdata, _a, expire_time, expire_day, val, err_2;
									return __generator(this, function (_b) {
											switch (_b.label) {
													case 0:
															close = config.close, vm = config.vm, expire = vm.expire;
															_b.label = 1;
													case 1:
															_b.trys.push([1, 4, , 5]);
															return [4, this.$request('setPawExpire', { expire: expire })];
													case 2:
															rdata = _b.sent();
															if (!rdata.status)
																	throw new Error(rdata);
															return [4, this.$request('getPasswordConfig', false)];
													case 3:
															_a = _b.sent(), expire_time = _a.expire_time, expire_day = _a.expire_day;
															close();
															val = expire > 0 ? "".concat(this.$formatTime(expire_time), " ( Exp in ").concat(expire_day, " days )") : lan.config.not_set;
															$('input[name="paw_expire_time"]').val(val);
															this.formColumns.paw_expire_time.day = expire;
															return [3, 5];
													case 4:
															err_2 = _b.sent();
															return [3, 5];
													case 5: return [2];
											}
									});
							}); },
					}).catch(function (err) { });
			};
			SafeConfig.prototype.setTempAuthView = function () {
					return __awaiter(this, void 0, void 0, function () {
							var _this = this;
							return __generator(this, function (_a) {
									this.$open({
											area: ['700px', '600px'],
											title: 'Temporary authorization management',
											content: "<div class=\"login_view_table pd15\">\n        <button class=\"btn btn-success btn-sm va0 create_temp_login\">Create authorization</button>\n        <div class=\"divtable mt10\">\n          <table class=\"table table-hover\">\n            <thead>\n              <tr>\n                <th>Login IP</th>\n                <th>Status</th>\n                <th>Login time</th>\n                <th>Expiration time</th>\n                <th style=\"text-align:right;\">Opt</th>\n              </tr>\n            </thead>\n            <tbody id=\"temp_login_view_tbody\">\n              <tr>\n                <td class=\"text-center\" colspan=\"5\">No Data</td>\n              </tr>\n            </tbody>\n          </table>\n          <div class=\"temp_login_view_page page\"></div>\n        </div>\n      </div>",
											success: function () {
													_this.reanderTempAuthList();
													$('.create_temp_login').on('click', function () {
															_this.$confirm({
																	title: 'Risk tips',
																	msg: "<span style=\"color:red\">Note 1: Abuse of temporary authorization may lead to security risks.</br>Note 2: Not publish temporary authorized connections in public</span></br>Temporary authorization connection is about to be created. Continue?",
															})
																	.then(function (res) {
																	return _this.$open({
																			area: '570px',
																			title: 'Create temporary authorization',
																			content: "<div class=\"bt-form create_temp_view\">\n                <div class=\"line\">\n                  <span class=\"tname\">Temporary authorized address</span>\n                  <div class=\"info-r ml0\">\n                    <textarea id=\"temp_link\" class=\"bt-input-text mr20\" style=\"margin: 0px;width: 500px;height: 50px;line-height: 19px;\"></textarea>\n                  </div>\n                </div>\n                <div class=\"line\">\n                  <button type=\"submit\" class=\"btn btn-success btn-sm btn-copy-temp-link\" data-clipboard-text=\"\">Copy address</button>\n                </div>\n                <ul class=\"help-info-text c7\">\n                  <li>The temporary authorization is valid within 1 hour after it is generated. It is a one-time authorization and will be invalid immediately after use</li>\n                  <li>Use temporary authorization to log in to the panel within 1 hour. Do not publish temporary authorization connection in public</li>\n                  <li>The authorized connection information is only displayed here once. If you forget it before use, please regenerate it</li>\n                </ul>\n              </div>",
																			success: function () { return __awaiter(_this, void 0, void 0, function () {
																					var rdata, temp_link, clipboard, clipboards;
																					var _this = this;
																					return __generator(this, function (_a) {
																							switch (_a.label) {
																									case 0: return [4, this.$request('setTempAuthLink')];
																									case 1:
																											rdata = _a.sent();
																											temp_link = "".concat(location.origin, "/login?tmp_token=").concat(rdata.token);
																											$('#temp_link').val(temp_link);
																											$('.btn-copy-temp-link').attr('data-clipboard-text', temp_link);
																											this.reanderTempAuthList();
																											return [4, this.$require('clipboard')];
																									case 2:
																											clipboard = (_a.sent()).clipboard;
																											clipboards = new clipboard('.btn');
																											clipboards.on('success', function (ev) {
																													_this.$msg({ status: true, msg: 'Copy succeeded!！' });
																													ev.clearSelection();
																											});
																											clipboards.on('error', function (ev) {
																													_this.$msg({ status: false, msg: 'Copy failed, please copy address manually' });
																											});
																											return [2];
																							}
																					});
																			}); },
																	});
															})
																	.catch(function (err) { });
													});
													$('#temp_login_view_tbody').on('click', '.logs_temp_login', function (ev) {
															var _a = $(ev.target).data(), id = _a.id, ip = _a.ip;
															_this.$open({
																	area: ['700px', '550px'],
																	title: "Operation logs [".concat(ip, "]"),
																	content: "<div class=\"pd15\">\n              <button class=\"btn btn-default btn-sm va0 refresh_login_logs\">Refresh logs</button>\n              <div class=\"divtable mt10 tablescroll\">\n                <table class=\"table table-hover\" id=\"logs_login_view_table\">\n                  <thead>\n                    <tr>\n                      <th width=\"90px\">Operation</th>\n                      <th width=\"140px\">Time</th>\n                      <th>logs</th>\n                    </tr>\n                  </thead>\n                  <tbody>\n                    <tr><td class=\"text-center\" colspan=\"3\">No Data</td></tr>\n                  </tbody>\n                </table>\n              </div>\n            </div>",
																	success: function () {
																			_this.reanderTempLogsList(id);
																			$('.refresh_login_logs').click(function () {
																					_this.reanderTempLogsList(id);
																			});
																			_this.fixedTableHead('#logs_login_view_table', '420px');
																	},
															}).catch(function (err) { });
													});
													$('#temp_login_view_tbody').on('click', '.remove_temp_login', function (ev) {
															_this.$confirm({
																	title: 'Remove unused licenses',
																	msg: 'Delete unused authorization record, continue?',
															})
																	.then(function (res) { return __awaiter(_this, void 0, void 0, function () {
																	var id, rdata;
																	return __generator(this, function (_a) {
																			switch (_a.label) {
																					case 0:
																							id = $(ev.target).data().id;
																							return [4, this.$request('removeTempAuthLink', { id: id })];
																					case 1:
																							rdata = _a.sent();
																							return [4, this.$delay()];
																					case 2:
																							_a.sent();
																							rdata.status && this.reanderTempAuthList();
																							return [2];
																			}
																	});
															}); })
																	.catch(function (err) { });
													});
													$('#temp_login_view_tbody').on('click', '.clear_temp_login', function (ev) {
															var _a = $(ev.target).data(), id = _a.id, ip = _a.ip;
															_this.$confirm({
																	title: 'Force logout [ ' + ip + ' ]',
																	msg: 'Confirm to force logout [ ' + ip + ' ] ?',
															})
																	.then(function () { return __awaiter(_this, void 0, void 0, function () {
																	var rdata;
																	return __generator(this, function (_a) {
																			switch (_a.label) {
																					case 0: return [4, this.$request('clearTempAuth', { id: id })];
																					case 1:
																							rdata = _a.sent();
																							return [4, this.$delay()];
																					case 2:
																							_a.sent();
																							rdata.status && this.reanderTempAuthList();
																							return [2];
																			}
																	});
															}); })
																	.catch(function (err) { });
													});
													$('.temp_login_view_page').on('click', 'a', function (ev) {
															ev.stopPropagation();
															ev.preventDefault();
															var href = $(ev.target).attr('href');
															var reg = /([0-9]*)$/;
															var p = reg.exec(href)[0];
															_this.reanderTempAuthList(p);
													});
											},
									}).catch(function (err) { });
									return [2];
							});
					});
			};
			SafeConfig.prototype.reanderTempAuthList = function (p) {
					if (p === void 0) { p = 1; }
					return __awaiter(this, void 0, void 0, function () {
							var html, rdata, data, page, _loop_1, this_1, i, err_3;
							return __generator(this, function (_a) {
									switch (_a.label) {
											case 0:
													html = '';
													_a.label = 1;
											case 1:
													_a.trys.push([1, 3, , 4]);
													return [4, this.$request('getTempAuthList', { p: p, rows: 10 })];
											case 2:
													rdata = _a.sent();
													data = rdata.data, page = rdata.page;
													if (data.length > 0) {
															_loop_1 = function (i) {
																	var item = data[i];
																	html += "<tr>\n          <td>".concat(item.login_addr || 'Not login', "</td>\n          <td>").concat((function () {
																			switch (item.state) {
																					case 0:
																							return '<a style="color:green;">Not login</a>';
																					case 1:
																							return '<a style="color:brown;">Logged in</a>';
																					case -1:
																							return '<a>Expired</a>';
																			}
																	})(), "</td>\n            <td>").concat(item.login_time == 0 ? 'Not login' : this_1.$formatTime(item.login_time), "</td>\n            <td>").concat(this_1.$formatTime(item.expire), "</td>\n            <td style=\"text-align:right;\">").concat((function () {
																			if (item.state != 1)
																					return "<a href=\"javascript:;\" class=\"btlink remove_temp_login\" data-ip=\"".concat(item.login_addr, "\" data-id=\"").concat(item.id, "\">Del</a>");
																			if (item.online_state)
																					return "<a href=\"javascript:;\" class=\"btlink clear_temp_login\" style=\"color:red\" data-ip=\"".concat(item.login_addr, "\" data-id=\"").concat(item.id, "\">Force logout</a>&nbsp;&nbsp;|&nbsp;&nbsp;\n                <a href=\"javascript:;\" class=\"btlink logs_temp_login\" data-ip=\"").concat(item.login_addr, "\" data-id=\"").concat(item.id, "\">Logs</a>");
																			return "<a href=\"javascript:;\" class=\"btlink logs_temp_login\" data-ip=\"".concat(item.login_addr, "\" data-id=\"").concat(item.id, "\">Logs</a>");
																	})(), "</td>\n          </tr>");
															};
															this_1 = this;
															for (i = 0; i < data.length; i++) {
																	_loop_1(i);
															}
													}
													else {
															html = '<tr><td class="text-center" colspan="5">No Data</td></tr>';
													}
													$('#temp_login_view_tbody').html(html);
													$('.temp_login_view_page').html(page);
													return [3, 4];
											case 3:
													err_3 = _a.sent();
													return [3, 4];
											case 4: return [2];
									}
							});
					});
			};
			SafeConfig.prototype.reanderTempLogsList = function (id) {
					return __awaiter(this, void 0, void 0, function () {
							var html, rdata, i, item, err_4;
							return __generator(this, function (_a) {
									switch (_a.label) {
											case 0:
													_a.trys.push([0, 2, , 3]);
													html = '';
													return [4, this.$request('getTempOperationLogs', { id: id })];
											case 1:
													rdata = _a.sent();
													if (rdata.length > 0) {
															for (i = 0; i < rdata.length; i++) {
																	item = rdata[i];
																	html += "<tr>\n            <td>".concat(item.type, "</td>\n            <td>").concat(item.addtime, "</td>\n            <td><span title=\"").concat(item.log, "\" style=\"white-space: pre;\">").concat(item.log, "</span></td>\n          </tr>");
															}
													}
													else {
															html = '<tr><td class="text-center" colspan="3">No Data</td></tr>';
													}
													$('#logs_login_view_table tbody').html(html);
													return [3, 3];
											case 2:
													err_4 = _a.sent();
													return [3, 3];
											case 3: return [2];
									}
							});
					});
			};
			return SafeConfig;
	}(configMixin_1.default));
	exports.default = SafeConfig;
});
