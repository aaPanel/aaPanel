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
define(["require", "exports", "./public/public"], function (require, exports, public_1) {
	"use strict";
	Object.defineProperty(exports, "__esModule", { value: true });
	public_1 = __importDefault(public_1);
	var NoticeConfig = (function (_super) {
			__extends(NoticeConfig, _super);
			function NoticeConfig() {
					var _this = _super.call(this) || this;
					_this.apiInfo = {
							getLoginAlarm: ['config/get_login_send', 'Getting login information, please wait...'],
							setLoginAlarm: ['config/set_login_send', lan.public.the],
							clearLoginAlarm: ['config/clear_login_send', lan.public.the],
							loginIpwhite: ['config/login_ipwhite', lan.public.the],
					};
					_this.info = {};
					_this.$apiInit(_this.apiInfo);
					return _this;
			}
			NoticeConfig.prototype.init = function (data) {
					var messageChannelInfo = data.messageChannelInfo, loginAlarmInfo = data.loginAlarmInfo;
					var setName = loginAlarmInfo.msg;
					var isSet = false;
					for (var key in messageChannelInfo) {
							var item = messageChannelInfo[key];
							if (!$.isEmptyObject(item.data) && item.name == setName) {
									isSet = true;
									this.setLinkText('.setAlarmMail', "".concat(item.title, " configured"), 'btlink');
									break;
							}
					}
					if (!isSet)
							this.setLinkText('.setAlarmMail', "Not configured", 'bt_warning');
					this.info = { messageChannelInfo: messageChannelInfo, loginAlarmInfo: loginAlarmInfo };
			};
			NoticeConfig.prototype.event = function () {
					var _this = this;
					$('.setAlarmMail, .setAlarmMailBtn').click(function () { return _this.setAlarmView(); });
			};
			NoticeConfig.prototype.setAlarmView = function () {
					return __awaiter(this, void 0, void 0, function () {
							var config, messageChannelInfo, isSet, key, item, error_1;
							var _this = this;
							return __generator(this, function (_a) {
									switch (_a.label) {
											case 0:
													config = this.info;
													messageChannelInfo = config.messageChannelInfo;
													isSet = false;
													for (key in messageChannelInfo) {
															item = messageChannelInfo[key];
															if (!$.isEmptyObject(item.data)) {
																	isSet = true;
																	break;
															}
													}
													if (!isSet)
															return [2, this.$msg({ msg: 'Please configure at least one alarm module in [Alarm > Alarm Settings].', icon: 2 })];
													_a.label = 1;
											case 1:
													_a.trys.push([1, 3, , 4]);
													return [4, this.$open({
																	area: ['800px', '540px'],
																	title: 'Login panel alarm',
																	content: "\n        <div class=\"bt-w-main\" style=\"height: 498px\">\n          <div class=\"bt-w-menu\" style=\"width: 140px;\">\n            <p class=\"bgw\">Alarm settings</p>\n            <p>IP whitelist</p>\n          </div>\n          <div class=\"bt-w-con pd15\" style=\"margin-left: 140px; height: 100%;\">\n            <div class=\"plugin_body\">\n              <div class=\"conter_box news-channel active\">\n                <div class=\"bt-form-new inline\"></div>                <div class=\"mt10 divtable\" id=\"config_server_table\">\n                  <div>\n                    <table class=\"table table-hover\" width=\"100%\">\n                      <thead>\n                        <tr>\n                          <th>Login info</th>\n                          <th class=\"text-right\" width=\"150\">Time</th>\n                        </tr>\n                      </thead>\n                      <tbody id=\"server_table\">\n                        <tr>\n                          <td class=\"text-center\" colspan=\"2\">No Data</td>\n                        </tr>\n                      </tbody>\n                    </table>\n                  </div>\n                  <div class=\"page\" id=\"server_table_page\"></div>\n                </div>\n                <ul class=\"help-info-text c7\" style=\"position: absolute; bottom: 15px; left: 15px;\">\n                  <li></li>\n                </ul>\n              </div>\n              <div class=\"conter_box\" style=\"display:none;height:440px\">\n                <div class=\"bt-form\">\n                  <div class=\"box\" style=\"display:inline-block;\">\n                    <input name=\"ip_write\" class=\"bt-input-text mr5\" type=\"text\" style=\"width: 220px;\" placeholder=\"Please enter the IP\" />\n                    <button class=\"btn btn-success btn-sm add_ip_write\">Add</button>\n                  </div>\n                  <div class=\"pull-right\">\n                    <button class=\"btn btn-default btn-sm text-right clear_all\">Clean All</button>\n                  </div>\n                  <div class=\"divtable mt10\">\n                    <table id=\"ip_write_table\" class=\"table table-hover\" width=\"100%\">\n                      <thead>\n                        <tr>\n                          <th width=\"60%\">IP</th>\n                          <th width=\"40%\" class=\"text-right\">Opt</th>\n                        </tr>\n                      </thead>\n                      <tbody>\n                        <tr>\n                          <td class=\"text-center\" colspan=\"2\">No Data</td>\n                        </tr>\n                      </tbody>\n                    </table>\n                  </div>\n                  <ul class=\"help-info-text c7\" style=\"position: absolute; bottom: 15px; left: 15px;\">\n                    <li>Only allow to set ipv4 whitelist</li>\n                  </ul>\n                </div>\n              </div>\n            </div>\n          </div>\n        </div>",
																	success: function () { return __awaiter(_this, void 0, void 0, function () {
																			var _this = this;
																			return __generator(this, function (_a) {
																					$('.bt-w-menu p').on('click', function (ev) { return __awaiter(_this, void 0, void 0, function () {
																							var el, index;
																							return __generator(this, function (_a) {
																									el = $(ev.target), index = el.index();
																									el.addClass('bgw').siblings().removeClass('bgw');
																									switch (index) {
																											case 0:
																													this.renderAlarmConfig();
																													this.reanderLoginTable();
																													break;
																											case 1:
																													this.reanderLoginIpTable();
																													break;
																									}
																									$('.conter_box').eq(index).show().siblings().hide();
																									return [2];
																							});
																					}); });
																					$('.news-channel .bt-form-new').on('change', 'input[type="checkbox"]', function (ev) { return __awaiter(_this, void 0, void 0, function () {
																							var $el, checked, type, name_1, res, error_2;
																							return __generator(this, function (_a) {
																									switch (_a.label) {
																											case 0:
																													$el = $(ev.currentTarget);
																													checked = $el.prop('checked');
																													type = $el.attr('name');
																													_a.label = 1;
																											case 1:
																													_a.trys.push([1, 3, , 4]);
																													name_1 = checked ? 'setLoginAlarm' : 'clearLoginAlarm';
																													return [4, this.$request(name_1, { type: type })];
																											case 2:
																													res = _a.sent();
																													if (!res.status) {
																															throw new Error(res);
																													}
																													if (checked) {
																															$('.news-channel .btswitch').prop('checked', false);
																															$el.prop('checked', true);
																															config.loginAlarmInfo.msg = type;
																													}
																													else {
																															config.loginAlarmInfo.msg = '';
																													}
																													this.init(config);
																													return [3, 4];
																											case 3:
																													error_2 = _a.sent();
																													$el.prop('checked', !checked);
																													return [3, 4];
																											case 4: return [2];
																									}
																							});
																					}); });
																					$('.add_ip_write').click(function () { return __awaiter(_this, void 0, void 0, function () {
																							var ip_write, ip, res, err_1;
																							return __generator(this, function (_a) {
																									switch (_a.label) {
																											case 0:
																													_a.trys.push([0, 3, , 4]);
																													ip_write = $('[name="ip_write"]');
																													ip = ip_write.val();
																													return [4, this.$verifySubmit(!this.$checkIp(ip), 'Please enter the correct IP')];
																											case 1:
																													_a.sent();
																													return [4, this.$request('loginIpwhite', { ip: ip, type: 'add' })];
																											case 2:
																													res = _a.sent();
																													if (!res.status)
																															return [2];
																													this.$delay();
																													this.reanderLoginIpTable();
																													ip_write.val('');
																													return [3, 4];
																											case 3:
																													err_1 = _a.sent();
																													return [3, 4];
																											case 4: return [2];
																									}
																							});
																					}); });
																					$('input[name="ip_write"]').keyup(function (e) {
																							if (e.keyCode == 13) {
																									$('.add_ip_write').click();
																							}
																					});
																					$('#ip_write_table').on('click', '.del_ip_write', function (ev) { return __awaiter(_this, void 0, void 0, function () {
																							var that, ip, res, err_2;
																							return __generator(this, function (_a) {
																									switch (_a.label) {
																											case 0:
																													that = $(ev.target);
																													ip = that.data('ip');
																													_a.label = 1;
																											case 1:
																													_a.trys.push([1, 4, , 5]);
																													return [4, this.$confirm({ title: 'Delete IP whitelist', msg: "Delete the IP whitelist [".concat(ip, "] and continue the operation?") })];
																											case 2:
																													_a.sent();
																													return [4, this.$request('loginIpwhite', { ip: ip, type: 'del' })];
																											case 3:
																													res = _a.sent();
																													if (!res.status)
																															return [2];
																													this.$delay();
																													this.reanderLoginIpTable();
																													return [3, 5];
																											case 4:
																													err_2 = _a.sent();
																													return [3, 5];
																											case 5: return [2];
																									}
																							});
																					}); });
																					$('.clear_all').click(function () { return __awaiter(_this, void 0, void 0, function () {
																							var res, err_3;
																							return __generator(this, function (_a) {
																									switch (_a.label) {
																											case 0:
																													_a.trys.push([0, 3, , 4]);
																													return [4, this.$confirm({ title: 'Tips', msg: 'Whether to clear the IP whitelist?' })];
																											case 1:
																													_a.sent();
																													return [4, this.$request('loginIpwhite', { type: 'clear' })];
																											case 2:
																													res = _a.sent();
																													if (!res.status)
																															return [2];
																													this.$delay();
																													this.reanderLoginIpTable();
																													return [3, 4];
																											case 3:
																													err_3 = _a.sent();
																													return [3, 4];
																											case 4: return [2];
																									}
																							});
																					}); });
																					$('#server_table_page').on('click', 'a', function (ev) { return __awaiter(_this, void 0, void 0, function () {
																							var page;
																							return __generator(this, function (_a) {
																									ev.stopPropagation();
																									ev.preventDefault();
																									page = $(ev.target)
																											.attr('href')
																											.match(/p=([0-9]*)/)[1];
																									this.reanderLoginTable(page);
																									return [2];
																							});
																					}); });
																					this.fixedTableHead('#config_server_table table', '348px');
																					this.fixedTableHead('#ip_write_table', '396px');
																					$('.bt-w-menu p').eq(0).click();
																					return [2];
																			});
																	}); },
															})];
											case 2:
													_a.sent();
													return [3, 4];
											case 3:
													error_1 = _a.sent();
													return [3, 4];
											case 4: return [2];
									}
							});
					});
			};
			NoticeConfig.prototype.renderAlarmConfig = function () {
					return __awaiter(this, void 0, void 0, function () {
							var _a, alarms, send, html, tits, cKey;
							return __generator(this, function (_b) {
									switch (_b.label) {
											case 0:
													return [4, Promise.all([this.$request(['config/get_msg_configs'], { loading: false, msg: false }), this.$request(['config/get_login_send'], { loading: false, msg: false })])];
											case 1:
													_a = _b.sent(), alarms = _a[0], send = _a[1];
													html = '';
													tits = [];
													cKey = send.msg;
													$.each(alarms, function (key, item) {
															var checked = cKey === item.name ? 'checked="checked"' : '';
															var title = item.title;
															html += "\n\t\t\t<div class=\"form-item\">\n\t\t\t\t<div class=\"form-label\" style=\"padding-right: 10px;\">Send to ".concat(title, "</div>\n\t\t\t\t<div class=\"form-content\">\n\t\t\t\t\t<input type=\"checkbox\" id=\"").concat(item.name, "_alarm\" class=\"btswitch btswitch-ios\" name=\"").concat(item.name, "\" ").concat(checked, " />\t\t\t\t\t<label class=\"btswitch-btn\" for=\"").concat(item.name, "_alarm\"></label>\n\t\t\t\t</div>\n\t\t\t</div>");
															tits.push(title);
													});
													$('.news-channel .bt-form-new').html(html);
													$('.news-channel .help-info-text li')
															.eq(0)
															.text("".concat(tits.join('/'), " can only open one at the same time"));
													return [2];
									}
							});
					});
			};
			NoticeConfig.prototype.reanderLoginTable = function (p) {
					if (p === void 0) { p = 1; }
					return __awaiter(this, void 0, void 0, function () {
							var rdata, html, i, item;
							return __generator(this, function (_a) {
									switch (_a.label) {
											case 0: return [4, this.$request(['config/get_login_log', 'Getting Logs list, please wait'], { p: p, limit: 4 })];
											case 1:
													rdata = _a.sent();
													if (!rdata.data)
															return [2, false];
													html = '';
													$('#server_table').empty();
													for (i = 0; i < rdata.data.length; i++) {
															item = rdata.data[i];
															html += "<tr>\n        <td>\n          <span title=\"".concat(item.log, "\">").concat(item.log, "</span>\n        </td>\n        <td class=\"text-right\">").concat(item.addtime, "</td>\n      </tr>");
													}
													!html && (html = "<tr><td class=\"text-center\" colspan=\"2\">No Data</td></tr>");
													$('#server_table').html(html);
													$('#server_table_page').html(rdata.page);
													return [2];
									}
							});
					});
			};
			NoticeConfig.prototype.reanderLoginIpTable = function () {
					return __awaiter(this, void 0, void 0, function () {
							var rdata, list, html, i, item, err_4;
							return __generator(this, function (_a) {
									switch (_a.label) {
											case 0:
													_a.trys.push([0, 2, , 3]);
													return [4, this.$request('loginIpwhite', { type: 'get' })];
											case 1:
													rdata = _a.sent();
													list = rdata.msg;
													html = '';
													for (i = 0; i < list.length; i++) {
															item = list[i];
															html += "<tr>\n          <td>".concat(item, "</td>\n          <td class=\"text-right\">\n            <a href=\"javascript:;\" class=\"btlink red del_ip_write\" data-ip=\"").concat(item, "\">Del</a>\n          </td>\n        </tr>");
													}
													!html && (html = "<tr><td colspan=\"2\" class=\"text-center\">No Data</td></tr>");
													$('#ip_write_table tbody').html(html);
													return [3, 3];
											case 2:
													err_4 = _a.sent();
													return [3, 3];
											case 3: return [2];
									}
							});
					});
			};
			return NoticeConfig;
	}(public_1.default));
	exports.default = NoticeConfig;
});
