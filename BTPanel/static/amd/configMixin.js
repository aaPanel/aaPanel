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
var __assign = (this && this.__assign) || function () {
	__assign = Object.assign || function(t) {
			for (var s, i = 1, n = arguments.length; i < n; i++) {
					s = arguments[i];
					for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
							t[p] = s[p];
			}
			return t;
	};
	return __assign.apply(this, arguments);
};
var __importDefault = (this && this.__importDefault) || function (mod) {
	return (mod && mod.__esModule) ? mod : { "default": mod };
};
define(["require", "exports", "./public/public"], function (require, exports, public_1) {
	"use strict";
	Object.defineProperty(exports, "__esModule", { value: true });
	public_1 = __importDefault(public_1);
	var ConfigMixin = (function (_super) {
			__extends(ConfigMixin, _super);
			function ConfigMixin() {
					return _super !== null && _super.apply(this, arguments) || this;
			}
			ConfigMixin.prototype.renderFormColumn = function (configInfo) {
					for (var key in configInfo) {
							if (Object.prototype.hasOwnProperty.call(configInfo, key)) {
									var value = configInfo[key].value;
									var el = $('input[name="' + key + '"]');
									var type = el.attr('type');
									if (type === 'checkbox') {
											el.prop('checked', value);
									}
									else {
											el.val(value);
									}
							}
					}
			};
			ConfigMixin.prototype.showCheckboxConfirm = function (data) {
					var _this = this;
					var e = data.e, api = data.api, config = data.config, param = data.data;
					return new Promise(function (resolve, reject) {
							_this.$confirm(__assign({}, config)).then(function (res) {
									return _this.changeCheckbox(e, api, param);
							}).then(function (res) {
									resolve(res);
							}).catch(function (err) {
									_this.changeReverseCheckbox(e);
									reject(err);
							});
					});
			};
			ConfigMixin.prototype.changeCheckbox = function (e, api, data) {
					var _this = this;
					if (data === void 0) { data = {}; }
					return new Promise(function (resolve, reject) {
							_this.$request(api, data).then(function (res) {
									if (res.status) {
											resolve(res);
									}
									else {
											throw new Error(res);
									}
							}).catch(function (err) {
									_this.changeReverseCheckbox(e);
									reject(err);
							});
					});
			};
			ConfigMixin.prototype.changeReverseCheckbox = function (e) {
					var $this = $(e.target);
					var checked = !$this.prop('checked');
					$this.prop('checked', checked);
			};
			ConfigMixin.prototype.setLayerVerticalCenter = function (layero) {
					var window_height = $(window).height();
					var height = layero.height();
					var top = (window_height - height) / 2;
					layero.css({
							'top': top + 'px'
					});
			};
			return ConfigMixin;
	}(public_1.default));
	exports.default = ConfigMixin;
});
