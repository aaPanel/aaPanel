$(
	(function () {
		$.fn.extend({
			fixedThead: function (options) {
				var _that = $(this);
				console.log(_that);
				var option = {
					height: 400,
					shadow: true,
					resize: true,
				};
				options = $.extend(option, options);
				if ($(this).find('table').length === 0) {
					return false;
				}
				var _height = $(this)[0].style.height,
					_table_config = _height.match(/([0-9]+)([%\w]+)/);
				if (_table_config === null) {
					_table_config = [null, options.height, 'px'];
				} else {
					$(this).css({
						boxSizing: 'content-box',
						paddingBottom: $(this).find('thead').height(),
					});
				}
				$(this).css({ position: 'relative' });
				var _thead = $(this).find('thead')[0].outerHTML,
					_tbody = $(this).find('tbody')[0].outerHTML,
					_thead_div = $('<div class="thead_div"><table class="table table-hover mb0"></table></div>'),
					_shadow_top = $('<div class="tbody_shadow_top"></div>'),
					_tbody_div = $(
						'<div class="tbody_div" style="height:' +
							_table_config[1] +
							_table_config[2] +
							';"><table class="table table-hover mb0" style="margin-top:-' +
							$(this).find('thead').height() +
							'px"></table></div>'
					),
					_shadow_bottom = $('<div class="tbody_shadow_bottom"></div>');
				_thead_div.find('table').append(_thead);
				_tbody_div.find('table').append(_thead);
				_tbody_div.find('table').append(_tbody);
				$(this).html('');
				$(this).append(_thead_div);
				$(this).append(_shadow_top);
				$(this).append(_tbody_div);
				$(this).append(_shadow_bottom);
				var _table_width = _that.find('.thead_div table')[0].offsetWidth,
					_body_width = _that.find('.tbody_div table')[0].offsetWidth,
					_length = _that.find('tbody tr:eq(0)>td').length;
				$(this)
					.find('tbody tr:eq(0)>td')
					.each(function (index, item) {
						var _item = _that.find('thead tr:eq(0)>th').eq(index);
						if (index === _length - 1) {
							_item.attr('width', $(item)[0].clientWidth + (_table_width - _body_width));
						} else {
							_item.attr('width', $(item)[0].offsetWidth);
						}
					});
				if (options.resize) {
					$(window).resize(function () {
						var _table_width = _that.find('.thead_div table')[0].offsetWidth,
							_body_width = _that.find('.tbody_div table')[0].offsetWidth,
							_length = _that.find('tbody tr:eq(0)>td').length;
						_that.find('tbody tr:eq(0)>td').each(function (index, item) {
							var _item = _that.find('thead tr:eq(0)>th').eq(index);
							if (index === _length - 1) {
								_item.attr('width', $(item)[0].clientWidth + (_table_width - _body_width));
							} else {
								_item.attr('width', $(item)[0].offsetWidth);
							}
						});
					});
				}
				if (options.shadow) {
					var table_body = $(this).find('.tbody_div')[0];
					if (_table_config[1] >= table_body.scrollHeight) {
						$(this).find('.tbody_shadow_top').hide();
						$(this).find('.tbody_shadow_bottom').hide();
					} else {
						$(this).find('.tbody_shadow_top').hide();
						$(this).find('.tbody_shadow_bottom').show();
					}
					$(this)
						.find('.tbody_div')
						.scroll(function (e) {
							var _scrollTop = $(this)[0].scrollTop,
								_scrollHeight = $(this)[0].scrollHeight,
								_clientHeight = $(this)[0].clientHeight,
								_shadow_top = _that.find('.tbody_shadow_top'),
								_shadow_bottom = _that.find('.tbody_shadow_bottom');
							if (_scrollTop == 0) {
								_shadow_top.hide();
								_shadow_bottom.show();
							} else if (_scrollTop > 0 && _scrollTop < _scrollHeight - _clientHeight) {
								_shadow_top.show();
								_shadow_bottom.show();
							} else if (_scrollTop == _scrollHeight - _clientHeight) {
								_shadow_top.show();
								_shadow_bottom.hide();
							}
						});
				}
			},
		});
	})(jQuery)
);

$(document).ready(function () {
	$('.sub-menu a.sub-menu-a').click(function () {
		$(this).next('.sub').slideToggle('slow').siblings('.sub:visible').slideUp('slow');
	});
});
var aceEditor = {
	layer_view: '',
	aceConfig: {}, //ace配置参数
	editor: null,
	supportedModes: {
		Apache_Conf: ['^htaccess|^htgroups|^htpasswd|^conf|htaccess|htgroups|htpasswd'],
		BatchFile: ['bat|cmd'],
		C_Cpp: ['cpp|c|cc|cxx|h|hh|hpp|ino'],
		CSharp: ['cs'],
		CSS: ['css'],
		Dockerfile: ['^Dockerfile'],
		golang: ['go'],
		HTML: ['html|htm|xhtml|vue|we|wpy'],
		Java: ['java'],
		JavaScript: ['js|jsm|jsx'],
		JSON: ['json'],
		JSP: ['jsp'],
		LESS: ['less'],
		Lua: ['lua'],
		Makefile: ['^Makefile|^GNUmakefile|^makefile|^OCamlMakefile|make'],
		Markdown: ['md|markdown'],
		MySQL: ['mysql'],
		Nginx: ['nginx|conf'],
		INI: ['ini|conf|cfg|prefs'],
		ObjectiveC: ['m|mm'],
		Perl: ['pl|pm'],
		Perl6: ['p6|pl6|pm6'],
		pgSQL: ['pgsql'],
		PHP_Laravel_blade: ['blade.php'],
		PHP: ['php|inc|phtml|shtml|php3|php4|php5|phps|phpt|aw|ctp|module'],
		Powershell: ['ps1'],
		Python: ['py'],
		R: ['r'],
		Ruby: ['rb|ru|gemspec|rake|^Guardfile|^Rakefile|^Gemfile'],
		Rust: ['rs'],
		SASS: ['sass'],
		SCSS: ['scss'],
		SH: ['sh|bash|^.bashrc'],
		SQL: ['sql'],
		SQLServer: ['sqlserver'],
		Swift: ['swift'],
		Text: ['txt'],
		Typescript: ['ts|typescript|str'],
		VBScript: ['vbs|vb'],
		Verilog: ['v|vh|sv|svh'],
		XML: ['xml|rdf|rss|wsdl|xslt|atom|mathml|mml|xul|xbl|xaml'],
		YAML: ['yaml|yml'],
		Compress: ['tar|zip|7z|rar|gz|arj|z'],
		images: ['icon|jpg|jpeg|png|bmp|gif|tif|emf'],
	},
	nameOverrides: {
		ObjectiveC: 'Objective-C',
		CSharp: 'C#',
		golang: 'Go',
		C_Cpp: 'C and C++',
		PHP_Laravel_blade: 'PHP (Blade Template)',
		Perl6: 'Perl 6',
	},
	pathAarry: [],
	encodingList: ['ASCII', 'UTF-8', 'GBK', 'GB2312', 'BIG5'],
	themeList: ['chrome', 'monokai'],
	fontSize: '13px',
	editorTheme: 'monokai', // 编辑器主题
	editorLength: 0,
	isAceView: true,
	ace_active: '',
	is_resizing: false,
	menu_path: '', // 当前文件目录根地址
	refresh_config: {
		// 刷新配置参数
		el: {}, // 需要重新获取的元素,为DOM对象
		path: '', // 需要获取的路径文件信息
		group: 1, // 当前列表层级，用来css固定结构
		is_empty: true,
	},
	editorStatus: 0, // 编辑器状态 还原: 0, 最大化: 1, 最小化:  -1
	// 事件编辑器-方法，事件绑定
	eventEditor: function () {
		var _this = this,
			_icon = '<span class="icon"><i class="glyphicon glyphicon-ok" aria-hidden="true"></i></span>';
		$(window).resize(function () {
			if (_this.ace_active != undefined) _this.setEditorView();
			if (aceEditor.editorStatus === 0 || aceEditor.editorStatus === 1) {
				var winW = $(this)[0].innerWidth,
					winH = $(this)[0].innerHeight;
				$('.aceEditors').css({
					top: aceEditor.editorStatus ? 0 : winH / 8,
					left: aceEditor.editorStatus ? 0 : winW / 8,
					width: aceEditor.editorStatus ? winW : (winW / 4) * 3,
					height: aceEditor.editorStatus ? winH : (winH / 4) * 3,
				});
				$('.aceEditors .layui-layer-content').css({ height: $('.aceEditors').height() - 42 });
			}
		});
		$(document).click(function (e) {
			$('.ace_toolbar_menu').hide();
			$('.ace_conter_editor .ace_editors').css('fontSize', _this.aceConfig.aceEditor.fontSize + 'px');
			$('.ace_toolbar_menu .menu-tabs,.ace_toolbar_menu .menu-encoding,.ace_toolbar_menu .menu-files').hide();
		});
		$('.ace_editor_main').on('click', function () {
			$('.ace_toolbar_menu').hide();
		});
		$('.ace_toolbar_menu').click(function (e) {
			e.stopPropagation();
			e.preventDefault();
		});
		// 显示工具条
		$('.ace_header .pull-down').click(function () {
			if ($(this).find('i').hasClass('glyphicon-menu-down')) {
				$('.ace_header').css({ top: '-35px' });
				$('.ace_overall').css({ top: '0' });
				$(this).css({ top: '35px', height: '40px', 'line-height': '40px' });
				$(this).find('i').addClass('glyphicon-menu-up').removeClass('glyphicon-menu-down');
			} else {
				$('.ace_header').css({ top: '0' });
				$('.ace_overall').css({ top: '35px' });
				$(this).removeAttr('style');
				$(this).find('i').addClass('glyphicon-menu-down').removeClass('glyphicon-menu-up');
			}
			_this.setEditorView();
		});
		// 切换TAB视图
		$('.ace_conter_menu').on('click', '.item', function (e) {
			var _id = $(this).attr('data-id'),
				_item = _this.editor['ace_editor_' + _id];
			$('.item_tab_' + _id)
				.addClass('active')
				.siblings()
				.removeClass('active');
			$('#ace_editor_' + _id)
				.addClass('active')
				.siblings()
				.removeClass('active');
			_this.ace_active = _id;
			_this.currentStatusBar(_id);
			_this.is_file_history(_item);
		});
		// 移上TAB按钮变化，仅文件被修改后
		$('.ace_conter_menu').on('mouseover', '.item .icon-tool', function () {
			var type = $(this).attr('data-file-state');
			if (type != '0') {
				$(this).removeClass('glyphicon-exclamation-sign').addClass('glyphicon-remove');
			}
		});
		// 移出tab按钮变化，仅文件被修改后
		$('.ace_conter_menu').on('mouseout', '.item .icon-tool', function () {
			var type = $(this).attr('data-file-state');
			if (type != '0') {
				$(this).removeClass('glyphicon-remove').addClass('glyphicon-exclamation-sign');
			}
		});
		// 关闭编辑视图
		$('.ace_conter_menu').on('click', '.item .icon-tool', function (e) {
			var file_type = $(this).attr('data-file-state');
			var file_title = $(this).attr('data-title');
			var _path = $(this).parent().parent().attr('title');
			var _id = $(this).parent().parent().attr('data-id');
			switch (file_type) {
				// 直接关闭
				case '0':
					_this.removeEditor(_id);
					break;
				// 未保存
				case '1':
					var loadT = layer.open({
						type: 1,
						area: ['400px', '180px'],
						title: 'Tips',
						content:
							'\
								<div class="ace-clear-form">\
									<div class="clear-icon"></div>\
									<div class="clear-title">Do you want to save changes to &nbsp<span class="size_ellipsis" style="max-width:150px;vertical-align: top;" title="' +
							file_title +
							'">' +
							file_title +
							'</span>&nbsp?</div>\
									<div class="clear-tips">If you don\'t save, the changes will be lost!</div>\
									<div class="ace-clear-btn" style="">\
										<button type="button" class="btn btn-sm btn-default" style="float:left" data-type="2">Dont save</button>\
										<button type="button" class="btn btn-sm btn-default" style="margin-right:10px;" data-type="1">Cancel</button>\
										<button type="button" class="btn btn-sm btn-success" data-type="0">Save</button>\
									</div>\
								</div>',
						success: function (layers, index) {
							$('.ace-clear-btn .btn').click(function () {
								var _type = $(this).attr('data-type'),
									editor_item = _this.editor['ace_editor_' + _id];
								switch (_type) {
									case '0': //保存文件
										_this.saveFileBody(
											{
												path: _path,
												data: editor_item.ace.getValue(),
												encoding: editor_item.encoding,
											},
											function (res) {
												layer.close(index);
												_this.removeEditor(editor_item.id);
												layer.msg(res.msg, { icon: 1 });
												editor_item.fileType = 0;
												$('.item_tab_' + editor_item.id + ' .icon-tool')
													.attr('data-file-state', '0')
													.removeClass('glyphicon-exclamation-sign')
													.addClass('glyphicon-remove');
											}
										);
										break;
									case '1': //关闭视图
										layer.close(index);
										break;
									case '2': //取消保存
										_this.removeEditor(_id);
										layer.close(index);
										break;
								}
							});
						},
					});
					break;
			}
			$('.ace_toolbar_menu').hide();
			$('.ace_toolbar_menu .menu-tabs,.ace_toolbar_menu .menu-encoding,.ace_toolbar_menu .menu-files').hide();
			e.stopPropagation();
			e.preventDefault();
		});
		$(window).keyup(function (e) {
			if (e.keyCode === 116 && $('#ace_conter').length == 1) {
				layer.msg('Unable to refresh in editor mode. Please close and try again');
			}
		});
		// 新建编辑器视图
		$('.ace_editor_add').click(function () {
			_this.addEditorView();
		});
		// 底部状态栏功能按钮
		$('.ace_conter_toolbar .pull-right span').click(function (e) {
			var _type = $(this).attr('data-type'),
				_item = _this.editor['ace_editor_' + _this.ace_active];
			$('.ace_toolbar_menu').show();
			switch (_type) {
				case 'cursor':
					$('.ace_toolbar_menu').hide();
					$('.ace_header .jumpLine').click();
					break;
				case 'history':
					$('.ace_toolbar_menu').hide();
					if (_item.historys.length === 0) {
						layer.msg(lan.public.history_file_empty, { icon: 0 });
						return false;
					}
					_this.layer_view = layer.open({
						type: 1,
						area: '550px',
						title: lan.public.history_version + '[ ' + _item.fileName + ' ]',
						skin: 'historys_layer',
						content:
							'<div class="pd20">\
													<div class="divtable" style="overflow:auto;height:450px; border: 1px solid #ddd;">\
														<table class="historys table table-hover" id="historys-table" style="border: none;">\
															<thead><tr><th>' +
							lan.public.file_name +
							'</th><th>' +
							lan.public.v_time +
							'</th><th style="text-align:right;">' +
							lan.public.operate +
							'</th></tr></thead>\
															<tbody></tbody>\
														</table>\
													</div>\
												</div>',
						success: function (layeo, index) {
							var _html = '';
							for (var i = 0; i < _item.historys.length; i++) {
								_html +=
									'<tr><td><span class="size_ellipsis" style="max-width:200px">' +
									_item.fileName +
									'</span></td><td>' +
									bt.format_data(_item.historys[i]) +
									'</td><td align="right"><a href="javascript:;" class="btlink open_history_file" data-time="' +
									_item.historys[i] +
									'">' +
									lan.public.open_file +
									'</a>&nbsp;&nbsp;|&nbsp;&nbsp;<a href="javascript:;" class="btlink recovery_file_historys" data-history="' +
									_item.historys[i] +
									'" data-path="' +
									_item.path +
									'">' +
									lan.public.restore +
									'</a></td></tr>';
							}
							if (_html === '') _html += '<tr><td colspan="3">' + lan.public.no_file_history + '</td></tr>';
							$('.historys tbody').html(_html);
							$('.historys_layer').css('top', $(window).height() / 2 - $('.historys_layer').height() / 2 + 'px');
							$('.open_history_file').click(function () {
								var _history = $(this).attr('data-time');
								_this.openHistoryEditorView({ filename: _item.path, history: _history }, function () {
									layer.close(index);
									$('.ace_conter_tips').show();
									$('.ace_conter_tips .tips').html(
										lan.public.read_only_file +
											_item.path +
											'，' +
											lan.public.history_v +
											' [ ' +
											bt.format_data(new Number(_history)) +
											' ]<a href="javascript:;" class="ml35 btlink" data-path="' +
											_item.path +
											'" data-history="' +
											_history +
											'">' +
											lan.public.restore_history +
											'</a>'
									);
								});
							});
							$('.recovery_file_historys').click(function () {
								_this.event_ecovery_file(this);
							});
							bt.fixed_table('historys-table');
						},
					});
					break;
				case 'tab':
					$('.ace_toolbar_menu .menu-tabs').show().siblings().hide();
					$('.tabsType')
						.find(_item.softTabs ? '[data-value="nbsp"]' : '[data-value="tabs"]')
						.addClass('active')
						.append(_icon);
					$('.tabsSize [data-value="' + _item.tabSize + '"]')
						.addClass('active')
						.append(_icon);
					break;
				case 'encoding':
					_this.getEncodingList(_item.encoding);
					$('.ace_toolbar_menu .menu-encoding').show().siblings().hide();
					break;
				case 'lang':
					$('.ace_toolbar_menu').hide();
					layer.msg(lan.public.can_not_switch_lan, { icon: 6 });
					break;
			}
			e.stopPropagation();
			e.preventDefault();
		});
		// 隐藏目录
		$('.tips_fold_icon .glyphicon').click(function () {
			if ($(this).hasClass('glyphicon-menu-left')) {
				$('.ace_conter_tips').css('right', '0');
				$('.tips_fold_icon').css('left', '0');
				$(this).removeClass('glyphicon-menu-left').addClass('glyphicon-menu-right');
			} else {
				$('.ace_conter_tips').css('right', '-100%');
				$('.tips_fold_icon').css('left', '-25px');
				$(this).removeClass('glyphicon-menu-right').addClass('glyphicon-menu-left');
			}
		});
		// 设置换行符
		$('.menu-tabs').on('click', 'li', function (e) {
			var _val = $(this).attr('data-value'),
				_item = _this.editor['ace_editor_' + _this.ace_active];
			if ($(this).parent().hasClass('tabsType')) {
				//_item.ace.getSession().setUseSoftTabs(_val == 'nbsp');
				_this.aceConfig.aceEditor.useSoftTabs = _val == 'nbsp';
				_item.softTabs = _val == 'nbsp';
			} else {
				//_item.ace.getSession().setTabSize(_val);
				_this.aceConfig.aceEditor.tabSize = _val;
				_item.tabSize = _val;
			}
			_this.saveAceConfig(_this.aceConfig, function (res) {
				if (res.status) {
					layer.msg('Successful setup', { icon: 1 });
				}
			});
			$(this).siblings().removeClass('active').find('.icon').remove();
			$(this).addClass('active').append(_icon);
			_this.currentStatusBar(_item.id);
			e.stopPropagation();
			e.preventDefault();
		});
		// 设置编码内容
		$('.menu-encoding').on('click', 'li', function (e) {
			var _item = _this.editor['ace_editor_' + _this.ace_active],
				_icon = '<span class="icon"><i class="glyphicon glyphicon-ok" aria-hidden="true"></i></span>';
			layer.msg(lan.public.set_file_encoding + ':' + $(this).attr('data-value'));
			$('.ace_conter_toolbar [data-type="encoding"]').html(lan.public.encoding + ': <i>' + $(this).attr('data-value') + '</i>');
			$(this).addClass('active').append(_icon).siblings().removeClass('active').find('span').remove();
			_item.encoding = $(this).attr('data-value');
			_this.saveFileMethod(_item);
		});
		// 搜索内容键盘事件
		$('.menu-files .menu-input').keyup(function () {
			_this.searchRelevance($(this).val());
			if ($(this).val != '') {
				$(this).next().show();
			} else {
				$(this).next().hide();
			}
		});
		// 清除搜索内容事件
		$('.menu-files .menu-conter .fa').click(function () {
			$('.menu-files .menu-input').val('').next().hide();
			_this.searchRelevance();
		});
		// 顶部状态栏
		$('.ace_header>span').click(function (e) {
			var type = $(this).attr('class'),
				editor_item = _this.editor['ace_editor_' + _this.ace_active];
			var _icon = '<span class="icon"><i class="glyphicon glyphicon-ok" aria-hidden="true"></i></span>';
			switch (type) {
				case 'saveFile': //保存当时文件
					_this.saveFileMethod(editor_item);
					break;
				case 'saveFileAll': //保存全部
					var loadT = layer.open({
						type: 1,
						area: ['350px', '180px'],
						title: 'Tips',
						content:
							'<div class="ace-clear-form">\
							<div class="clear-icon"></div>\
							<div class="clear-title">Do you want to save changes to all files?</div>\
							<div class="clear-tips">If you don\'t save, the changes will be lost!</div>\
							<div class="ace-clear-btn" style="">\
								<button type="button" class="btn btn-sm btn-default clear-btn" style="margin-right:10px;" >Cancel</button>\
								<button type="button" class="btn btn-sm btn-success save-all-btn">Save</button>\
							</div>\
						</div>',
						success: function (layers, index) {
							$('.clear-btn').click(function () {
								layer.close(index);
							});
							$('.save-all-btn').click(function () {
								var _arry = [],
									editor = aceEditor['editor'];
								for (var item in editor) {
									_arry.push({
										path: editor[item]['path'],
										data: editor[item]['ace'].getValue(),
										encoding: editor[item]['encoding'],
									});
								}
								_this.saveAllFileBody(_arry, function () {
									$('.ace_conter_menu>.item').each(function (el, index) {
										var _id = $(this).attr('data-id');
										$(this).find('i').attr('data-file-state', '0').removeClass('glyphicon-exclamation-sign').addClass('glyphicon-remove');
										aceEditor.editor['ace_editor_' + _id].fileType = 0;
									});
									layer.close(index);
								});
							});
						},
					});
					break;
				case 'refreshs': //刷新文件
					if (editor_item.fileType === 0) {
						aceEditor.getFileBody({ path: editor_item.path }, function (res) {
							editor_item.ace.setValue(res.data);
							editor_item.fileType = 0;
							$('.item_tab_' + editor_item.id + ' .icon-tool')
								.attr('data-file-state', '0')
								.removeClass('glyphicon-exclamation-sign')
								.addClass('glyphicon-remove');
							layer.msg('Refresh successfully', { icon: 1 });
						});
						return false;
					}
					var loadT = layer.open({
						type: 1,
						//area: ['350px', '180px'],
						title: 'Tips',
						content:
							'<div class="ace-clear-form">\
							<div class="clear-icon"></div>\
							<div class="clear-title">Whether to refresh the current file</div>\
							<div class="clear-tips">Refreshing the current file will overwrite the current modification and continue!</div>\
							<div class="ace-clear-btn" style="">\
								<button type="button" class="btn btn-sm btn-default clear-btn" style="margin-right:10px;" >Cancel</button>\
								<button type="button" class="btn btn-sm btn-success save-all-btn">Save</button>\
							</div>\
						</div>',
						success: function (layers, index) {
							$('.clear-btn').click(function () {
								layer.close(index);
							});
							$('.save-all-btn').click(function () {
								aceEditor.getFileBody({ path: editor_item.path }, function (res) {
									layer.close(index);
									editor_item.ace.setValue(res.data);
									editor_item.fileType == 0;
									$('.item_tab_' + editor_item.id + ' .icon-tool')
										.attr('data-file-state', '0')
										.removeClass('glyphicon-exclamation-sign')
										.addClass('glyphicon-remove');
									layer.msg('Refresh successfully', { icon: 1 });
								});
							});
						},
					});
					break;
				// 搜索
				case 'searchs':
					editor_item.ace.execCommand('find');
					break;
				// 替换
				case 'replaces':
					editor_item.ace.execCommand('replace');
					break;
				// 跳转行
				case 'jumpLine':
					$('.ace_toolbar_menu').show().find('.menu-jumpLine').show().siblings().hide();
					$('.set_jump_line input').val('').focus();
					$('.set_jump_line .btn-save')
						.unbind('click')
						.click(function () {
							var _jump_line = $('.set_jump_line input').val();
							editor_item.ace.gotoLine(_jump_line);
							$('.ace_toolbar_menu').hide();
						});
					$('.set_jump_line input')
						.unbind('keypress keydown keyup')
						.on('keypress keydown keyup', function (e) {
							if (e.keyCode == 13 || (e.keyCode >= 48 && e.keyCode <= 57) || (e.keyCode >= 96 && e.keyCode <= 105)) {
								var _jump_line = $('.set_jump_line input').val();
								if (_jump_line == '' && typeof parseInt(_jump_line) != 'number') return false;
								editor_item.ace.gotoLine(_jump_line);
							}
						});
					break;
				// 字体
				case 'fontSize':
					$('.ace_toolbar_menu').show().find('.menu-fontSize').show().siblings().hide();
					$('.menu-fontSize .set_font_size input').val(_this.aceConfig.aceEditor.fontSize).focus();
					$('.menu-fontSize set_font_size input')
						.unbind('keypress onkeydown')
						.on('keypress onkeydown', function (e) {
							var _val = $(this).val();
							if (_val == '') {
								$(this).css('border', '1px solid red');
								$(this).next('.tips').text('Font setting range 12-45');
							} else if (!isNaN(_val)) {
								$(this).removeAttr('style');
								if (parseInt(_val) > 11 && parseInt(_val) < 45) {
									$('.ace_conter_editor .ace_editors').css('fontSize', _val + 'px');
								} else {
									$('.ace_conter_editor .ace_editors').css('fontSize', '13px');
									$(this).css('border', '1px solid red');
									$(this).next('.tips').text('Font setting range 12-45');
								}
							} else {
								$(this).css('border', '1px solid red');
								$(this).next('.tips').text('Font setting range 12-45');
							}
							e.stopPropagation();
							e.preventDefault();
						});
					$('.menu-fontSize .menu-conter .set_font_size input')
						.unbind('change')
						.change(function () {
							var _val = $(this).val();
							$('.ace_conter_editor .ace_editors').css('fontSize', _val + 'px');
						});
					$('.set_font_size .btn-save')
						.unbind('click')
						.click(function () {
							var _fontSize = $('.set_font_size input').val();
							_this.aceConfig.aceEditor.fontSize = parseInt(_fontSize);
							_this.saveAceConfig(_this.aceConfig, function (res) {
								if (res.status) {
									$('.ace_editors').css('fontSize', _fontSize + 'px');
									layer.msg('Successful setup', { icon: 1 });
									$('.ace_toolbar_menu').hide();
								}
							});
						});

					break;
				//主题
				case 'themes':
					$('.ace_toolbar_menu').show().find('.menu-themes').show().siblings().hide();
					var _html = '',
						_arry = ['White', 'Black'];
					for (var i = 0; i < _this.themeList.length; i++) {
						if (_this.themeList[i] != _this.aceConfig.aceEditor.editorTheme) {
							_html += '<li data-value="' + _this.themeList[i] + '">' + _this.themeList[i] + '【' + _arry[i] + '】</li>';
						} else {
							_html += '<li data-value="' + _this.themeList[i] + '" class="active">' + _this.themeList[i] + '【' + _arry[i] + '】' + _icon + '</li>';
						}
					}
					$('.menu-themes ul').html(_html);
					$('.menu-themes ul li').click(function () {
						var _theme = $(this).attr('data-value');
						$(this).addClass('active').append(_icon).siblings().removeClass('active').find('.icon').remove();
						_this.aceConfig.aceEditor.editorTheme = _theme;
						_this.saveAceConfig(_this.aceConfig, function (res) {
							for (var item in _this.editor) {
								_this.editor[item].ace.setTheme('ace/theme/' + _theme);
							}
							layer.msg('Successful setup', { icon: 1 });
						});
					});
					break;
				case 'setUp':
					$('.ace_toolbar_menu').show().find('.menu-setUp').show().siblings().hide();
					$('.menu-setUp .editor_menu li').each(function (index, el) {
						var _type = _this.aceConfig.aceEditor[$(el).attr('data-type')];
						if (_type) $(el).addClass('active').append(_icon);
					});
					$('.menu-setUp .editor_menu li')
						.unbind('click')
						.click(function () {
							var _type = $(this).attr('data-type');
							_this.aceConfig.aceEditor[_type] = !$(this).hasClass('active');
							if ($(this).hasClass('active')) {
								$(this).removeClass('active').find('.icon').remove();
							} else {
								$(this).addClass('active').append(_icon);
							}
							_this.saveAceConfig(_this.aceConfig, function (res) {
								for (var item in _this.editor) {
									_this.editor[item].ace.setOption(_type, _this.aceConfig.aceEditor[_type]);
								}
								layer.msg('Successful setup', { icon: 1 });
							});
						});
					break;
				case 'helps':
					layer.open({
						type: 1,
						area: '1300px',
						title: 'Help',
						content:
							'<div class="helps_conter">\
							<div class="helps_left">\
								<div class="helps_item">Common shortcuts:</div>\
								<div class="helps_box">\
									ctrl+s&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Save</br>\
									ctrl+a&nbsp;&nbsp;Select all&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ctrl+x&nbsp;&nbsp;Cut</br>\
									ctrl+c&nbsp;&nbsp;Copy&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ctrl+v&nbsp;&nbsp;Paste</br>\
									ctrl+z&nbsp;&nbsp;Cancel&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ctrl+y&nbsp;&nbsp;Anti-cancel</br>\
									ctrl+f&nbsp;&nbsp;Find&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ctrl+alt+f&nbsp;&nbsp;Replace</br>\
									win+alt+0&nbsp;&nbsp;Collapse all</br>\
									win+alt+shift+0&nbsp;&nbsp;Expand all</br>\
									esc&nbsp;&nbsp;[Exit the search and cancel the automatic prompt...]</br>\
									ctrl-shift-s&nbsp;&nbsp;Preview</br>\
									ctrl-shift-e&nbsp;&nbsp;Show & close function\
								</div>\
								<div class="helps_item">Select:</div>\
								<div class="helps_box">\
									Mouse frame selection -- drag</br>\
									shift+home/end/up/left/down/right</br>\
									shift+pageUp/PageDown&nbsp;&nbsp;Scroll up and down</br>\
									ctrl+shift+ home/end&nbsp;&nbsp;Current cursor to the end of the head</br>\
									alt+ Mouse drag&nbsp;&nbsp;Block selection</br>\
									ctrl+alt+g&nbsp;&nbsp;Batch select current and enter multi-tab editing</br>\
								</div>\
							</div>\
							<div class="helps_left">\
								<div class="helps_item">Cursor movement:</div>\
								<div class="helps_box">\
									home/end/up/left/down/right</br>\
									ctrl+home/end&nbsp;&nbsp;Cursor moves to the beginning/end of the document</br>\
									ctrl+p&nbsp;&nbsp;Jump to the matching tag</br>\
									pageUp/PageDown&nbsp;&nbsp;Cursor up and down</br>\
									alt+left/right&nbsp;&nbsp;Cursor moves to the top of the line</br>\
									shift+left/right&nbsp;&nbsp;Cursor moves to the beginning & end of the line</br>\
									ctrl+l&nbsp;&nbsp;Jump to the specified line</br>\
									ctrl+alt+up/down&nbsp;&nbsp;Add cursor to the top (bottom)</br>\
								</div>\
								<div class="helps_item">Edit:</div>\
								<div class="helps_box">\
									ctrl+/&nbsp;&nbsp;Comment & Uncomment&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ctrl+alt+a&nbsp;&nbsp;Align left and right</br>\
									table&nbsp;&nbsp;Tab alignment&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;shift+table&nbsp;&nbsp;Overall advancement table</br>\
									delete&nbsp;&nbsp;Delete&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ctrl+d&nbsp;&nbsp;Delete entire line</br>\
									ctrl+delete&nbsp;&nbsp;Delete the word on the right side of the line</br>\
									ctrl/shift+backspace&nbsp;&nbsp;Delete the word on the left</br>\
									alt+shift+up/down&nbsp;&nbsp;Copy the line and add it to the top (below)</br>\
									alt+delete&nbsp;&nbsp;Delete the right side of the cursor</br>\
									alt+up/down&nbsp;&nbsp;The current line is swapped with the previous line (the next line)</br>\
									ctrl+shift+d&nbsp;&nbsp;Copy the line and add it below</br>\
									ctrl+delete&nbsp;&nbsp;Delete the word on the right</br>\
									ctrl+shift+u&nbsp;&nbsp;Convert to lowercase</br>\
									ctrl+u&nbsp;&nbsp;Convert selected content to uppercase</br>\
								</div>\
							</div>\
						</div>',
					});
					break;
			}
			e.stopPropagation();
			e.preventDefault();
		});
		// 菜单状态
		$('.ace_toolbar_menu').click(function (e) {
			e.stopPropagation();
			e.preventDefault();
		});
		// 文件目录选择
		$('.ace_catalogue_list').on('click', '.has-children .file_fold', function (e) {
			var _layers = $(this).attr('data-layer'),
				_type = $(this).find('data-type'),
				_path = $(this).parent().attr('data-menu-path'),
				_menu = $(this).find('.glyphicon'),
				_group = parseInt($(this).attr('data-group')),
				_file = $(this).attr('data-file'),
				_tath = $(this);
			var _active = $('.ace_catalogue_list .has-children .file_fold.edit_file_group');
			if (_active.length > 0 && $(this).attr('data-edit') === undefined) {
				switch (_active.attr('data-edit')) {
					case '2':
						_active.find('.file_input').siblings().show();
						_active.find('.file_input').remove();
						_active.removeClass('edit_file_group').removeAttr('data-edit');
						break;
					case '1':
					case '0':
						_active.parent().remove();
						break;
				}
				layer.closeAll('tips');
			}
			//$('.ace_catalogue_menu').hide();
			$('.ace_toolbar_menu').hide();
			$('.ace_toolbar_menu .menu-tabs,.ace_toolbar_menu .menu-encoding,.ace_toolbar_menu .menu-files').hide();
			if ($(this).hasClass('edit_file_group')) return false;
			$('.ace_catalogue_list .has-children .file_fold').removeClass('bg');
			$(this).addClass('bg');
			if ($(this).attr('data-file') == 'Dir') {
				if (_menu.hasClass('glyphicon-menu-right')) {
					_menu.removeClass('glyphicon-menu-right').addClass('glyphicon-menu-down');
					$(this).next().show();
					if ($(this).next().find('li').length == 0) _this.reader_file_dir_menu({ el: $(this).next(), path: _path, group: _group + 1 });
				} else {
					_menu.removeClass('glyphicon-menu-down').addClass('glyphicon-menu-right');
					$(this).next().hide();
				}
			} else {
				_this.openEditorView(_path, function (res) {
					if (res.status) _tath.addClass('active');
				});
			}
			e.stopPropagation();
			e.preventDefault();
		});
		// 禁用目录选择
		$('.ace_catalogue').bind('selectstart', function (e) {
			var omitformtags = ['input', 'textarea'];
			omitformtags = '|' + omitformtags.join('|') + '|';
			if (omitformtags.indexOf('|' + e.target.tagName.toLowerCase() + '|') == -1) {
				return false;
			} else {
				return true;
			}
		});
		// 返回目录（文件目录主菜单）
		$('.ace_dir_tools').on('click', '.upper_level', function () {
			var _paths = $(this).attr('data-menu-path');
			_this.reader_file_dir_menu({ path: _paths, is_empty: true });
			$('.ace_catalogue_title')
				.html('Dir: ' + _paths)
				.attr('title', _paths);
		});
		// 新建文件（文件目录主菜单）
		$('.ace_dir_tools').on('click', '.new_folder', function (e) {
			var _paths = $(this).parent().find('.upper_level').attr('data-menu-path');
			$(this).find('.folder_down_up').show();
			$(document).click(function () {
				$('.folder_down_up').hide();
				$(this).unbind('click');
				return false;
			});
			$('.ace_toolbar_menu').hide();
			$('.ace_catalogue_menu').hide();
			$('.ace_toolbar_menu .menu-tabs,.ace_toolbar_menu .menu-encoding,.ace_toolbar_menu .menu-files').hide();
			e.stopPropagation();
			e.preventDefault();
		});
		// 刷新列表 (文件目录主菜单)
		$('.ace_dir_tools').on('click', '.refresh_dir', function (e) {
			_this.refresh_config = {
				el: $('.cd-accordion-menu')[0],
				path: $('.ace_catalogue_title').attr('title'),
				group: 1,
				is_empty: true,
			};
			_this.reader_file_dir_menu(_this.refresh_config, function () {
				layer.msg('Refresh success!', { icon: 1 });
			});
		});
		// 搜索内容 (文件目录主菜单)
		$('.ace_dir_tools').on('click', '.search_file', function (e) {
			if ($(this).parent().find('.search_input_view').length == 0) {
				$(this).siblings('div').hide();
				$(this).css('color', '#ec4545').attr({ title: 'Close' }).find('.glyphicon').removeClass('glyphicon-search').addClass('glyphicon-remove').next().text('Close');
				$(this).before('<div class="search_input_title">Search Catalog File</div>');
				$(this).after(
					'<div class="search_input_view">\
					<form>\
                        <input type="text" id="search_input_val" class="ser-text pull-left" placeholder="">\
                        <button type="button" class="ser-sub pull-left"></button>\
                    </form>\
                    <div class="search_boxs">\
                        <input id="search_alls" type="checkbox">\
                        <label for="search_alls"><span>Include Subdirectory Files</span></label>\
                    </div>\
                </div>'
				);
				$('.ace_catalogue_list').css('top', '150px');
				$('.ace_dir_tools').css('height', '110px');
				$('.cd-accordion-menu').empty();
			} else {
				$(this).siblings('div').show();
				$(this).parent().find('.search_input_view,.search_input_title').remove();
				$(this).removeAttr('style').attr({ title: 'Search Content' }).find('.glyphicon').removeClass('glyphicon-remove').addClass('glyphicon-search').next().text('Search');
				$('.ace_catalogue_list').removeAttr('style');
				$('.ace_dir_tools').removeAttr('style');
				_this.refresh_config = {
					el: $('.cd-accordion-menu')[0],
					path: $('.ace_catalogue_title').attr('title'),
					group: 1,
					is_empty: true,
				};
				_this.reader_file_dir_menu(_this.refresh_config);
			}
		});

		// 搜索文件内容
		$('.ace_dir_tools').on('click', '.search_input_view button', function (e) {
			var path = _this.menu_path,
				search = $('#search_input_val').val();
			_this.reader_file_dir_menu({
				el: $('.cd-accordion-menu')[0],
				path: path,
				group: 1,
				search: search,
				all: $('#search_alls').is(':checked') ? 'True' : 'False',
				is_empty: true,
			});
		});
		// 当前根目录操作，新建文件或目录
		$('.ace_dir_tools').on('click', '.folder_down_up li', function (e) {
			var _type = parseInt($(this).attr('data-type'));
			switch (_type) {
				case 2:
					_this.newly_file_type_dom($('.cd-accordion-menu'), 0, 0);
					break;
				case 3:
					_this.newly_file_type_dom($('.cd-accordion-menu'), 0, 1);
					break;
			}
			_this.refresh_config = {
				el: $('.cd-accordion-menu')[0],
				path: $('.ace_catalogue_title').attr('title'),
				group: 1,
				is_empty: true,
			};
			$(this).parent().hide();
			$('.ace_toolbar_menu').hide();
			$('.ace_toolbar_menu .menu-tabs,.ace_toolbar_menu .menu-encoding,.ace_toolbar_menu .menu-files').hide();
			e.preventDefault();
			e.stopPropagation();
		});

		// 返回目录
		$('.ace_catalogue_list').on('click', '.has-children.upper_level', function (e) {
			var _paths = $(this).attr('data-menu-path');
			_this.reader_file_dir_menu({ path: _paths, is_empty: true });
			$('.ace_catalogue_title')
				.html(lan.public.dir + ': ' + _paths)
				.attr('title', _paths);
		});
		// 移动编辑器文件目录
		$('.ace_catalogue_drag_icon .drag_icon_conter').on('mousedown', function (e) {
			var _left = $('.aceEditors')[0].offsetLeft;
			$('.ace_gutter-layer').css('cursor', 'col-resize');
			$('#ace_conter')
				.unbind()
				.on('mousemove', function (ev) {
					var _width = ev.clientX + 1 - _left;
					if (_width >= 250 && _width <= 400) {
						$('.ace_catalogue').css('width', _width);
						$('.ace_editor_main').css('marginLeft', _width);
						$('.ace_catalogue_drag_icon ').css('left', _width);
						$('.file_fold .newly_file_input').width(
							$('.file_fold .newly_file_input').parent().parent().parent().width() - ($('.file_fold .newly_file_input').parent().parent().attr('data-group') * 15 - 5) - 20 - 30 - 53
						);
					}
				})
				.on('mouseup', function (ev) {
					$('.ace_gutter-layer').css('cursor', 'inherit');
					$(this).unbind('mouseup mousemove');
				});
		});
		// 收藏目录显示和隐藏
		$('.ace_catalogue_drag_icon .fold_icon_conter').on('click', function (e) {
			if ($('.ace_overall').hasClass('active')) {
				$('.ace_overall').removeClass('active');
				$('.ace_catalogue').css('left', '0');
				$(this).removeClass('active').attr('title', lan.public.hide_dir);
				$('.ace_editor_main').css('marginLeft', $('.ace_catalogue').width());
			} else {
				$('.ace_overall').addClass('active');
				$('.ace_catalogue').css('left', '-' + $('.ace_catalogue').width() + 'px');
				$(this).addClass('active').attr('title', lan.public.show_file_dir);
				$('.ace_editor_main').css('marginLeft', 0);
			}
		});
		// 恢复历史文件
		$('.ace_conter_tips').on('click', 'a', function () {
			_this.event_ecovery_file(this);
		});
		// 右键菜单
		$('.ace_catalogue_list').on('mousedown', '.has-children .file_fold', function (e) {
			var x = e.clientX,
				y = e.clientY,
				_left = $('.aceEditors')[0].offsetLeft,
				_top = $('.aceEditors')[0].offsetTop,
				_that = $('.ace_catalogue_list .has-children .file_fold'),
				_active = $('.ace_catalogue_list .has-children .file_fold.edit_file_group');
			$('.ace_toolbar_menu').hide();
			if (e.which === 3) {
				if ($(this).hasClass('edit_file_group')) return false;
				$('.ace_catalogue_menu').css({ display: 'block', left: x - _left, top: y - _top });
				_that.removeClass('bg');
				$(this).addClass('bg');
				_active.attr('data-edit') != '2' ? _active.parent().remove() : '';
				_that.removeClass('edit_file_group').removeAttr('data-edit');
				_that.find('.file_input').siblings().show();
				_that.find('.file_input').remove();
				$('.ace_catalogue_menu li').show();
				if ($(this).attr('data-file') == 'Dir') {
					$('.ace_catalogue_menu li:nth-child(6)').hide();
				} else {
					$('.ace_catalogue_menu li:nth-child(-n+4)').hide();
				}
				$(document).click(function () {
					$('.ace_catalogue_menu').hide();
					$(this).unbind('click');
					return false;
				});
				_this.refresh_config = {
					el: $(this).parent().parent()[0],
					path: _this.get_file_dir($(this).parent().attr('data-menu-path'), 1),
					group: parseInt($(this).attr('data-group')),
					is_empty: true,
				};
			}
		});
		// 文件目录右键功能
		$('.ace_catalogue_menu li').click(function (e) {
			_this.newly_file_type(this);
		});
		// 新建、重命名鼠标事件
		$('.ace_catalogue_list').on('click', '.has-children .edit_file_group .glyphicon-ok', function () {
			var _file_or_dir = $(this).parent().find('input').val(),
				_file_type = $(this).parent().parent().attr('data-file'),
				_path = $('.has-children .file_fold.bg').parent().attr('data-menu-path'),
				_type = parseInt($(this).parent().parent().attr('data-edit'));
			if ($(this).parent().parent().parent().attr('data-menu-path') === undefined && parseInt($(this).parent().parent().attr('data-group')) === 1) {
				_path = $('.ace_catalogue_title').attr('title');
			}
			if (_file_or_dir === '') {
				$(this).prev().css('border', '1px solid #f34a4a');
				layer.tips(_type === 0 ? lan.public.dir_cannot_empty : _type === 1 ? lan.public.file_name_empty_err : lan.public.new_name_err, $(this).prev(), { tips: [1, '#f34a4a'], time: 0 });
				return false;
			} else if ($(this).prev().attr('data-type') === 0) {
				return false;
			}
			switch (_type) {
				case 0: //新建文件夹
					_this.event_create_dir({ path: _path + '/' + _file_or_dir });
					break;
				case 1: //新建文件
					_this.event_create_file({ path: _path + '/' + _file_or_dir });
					break;
				case 2: //重命名
					_this.event_rename_currency({ sfile: _path, dfile: _this.get_file_dir(_path, 1) + '/' + _file_or_dir });
					break;
			}
		});
		// 新建、重命名键盘事件
		$('.ace_catalogue_list').on('keyup', '.has-children .edit_file_group input', function (e) {
			var _type = $(this).parent().parent().attr('data-edit'),
				_arry = $('.has-children .file_fold.bg+ul>li');
			if (_arry.length == 0 && $(this).parent().parent().attr('data-group') == 1) _arry = $('.cd-accordion-menu>li');
			if (_type != 2) {
				for (var i = 0; i < _arry.length; i++) {
					if ($(_arry[i]).find('.file_title span').html() === $(this).val()) {
						$(this).css('border', '1px solid #f34a4a');
						$(this).attr('data-type', 0);
						layer.tips(_type == 0 ? lan.public.same_name_dir : lan.public.same_name_file, $(this)[0], { tips: [1, '#f34a4a'], time: 0 });
						return false;
					}
				}
			}
			if (_type == 1 && $(this).val().indexOf('.'))
				$(this)
					.prev()
					.removeAttr('class')
					.addClass(_this.get_file_suffix($(this).val()) + '-icon');
			$(this).attr('data-type', 1);
			$(this).css('border', '1px solid #528bff');
			layer.closeAll('tips');
			if (e.keyCode === 13) $(this).next().click();
			$('.ace_toolbar_menu').hide();
			$('.ace_toolbar_menu .menu-tabs,.ace_toolbar_menu .menu-encoding,.ace_toolbar_menu .menu-files').hide();
			e.stopPropagation();
			e.preventDefault();
		});
		// 新建、重命名鼠标点击取消事件
		$('.ace_catalogue_list').on('click', '.has-children .edit_file_group .glyphicon-remove', function () {
			layer.closeAll('tips');
			if ($(this).parent().parent().parent().attr('data-menu-path')) {
				$(this).parent().parent().removeClass('edit_file_group').removeAttr('data-edit');
				$(this).parent().siblings().show();
				$(this).parent().remove();
				return false;
			}
			$(this).parent().parent().parent().remove();
		});
		//屏蔽浏览器右键菜单
		$('.ace_catalogue_list')[0].oncontextmenu = function () {
			return false;
		};
		this.setEditorView();
		this.reader_file_dir_menu();
	},
	// 	设置本地存储，设置类型type：session或local
	setStorage: function (type, key, val) {
		if (type != 'local' && type != 'session') (val = key), (key = type), (type = 'session');
		window[type + 'Storage'].setItem(key, val);
	},
	//获取指定本地存储，设置类型type：session或local
	getStorage: function (type, key) {
		if (type != 'local' && type != 'session') (key = type), (type = 'session');
		return window[type + 'Storage'].getItem(key);
	},
	//删除指定本地存储，设置类型type：session或local
	removeStorage: function (type, key) {
		if (type != 'local' && type != 'session') (key = type), (type = 'session');
		window[type + 'Storage'].removeItem(key);
	},
	// 	删除指定类型的所有存储信息
	clearStorage: function (type) {
		if (type != 'local' && type != 'session') (key = type), (type = 'session');
		window[type + 'Storage'].clear();
	},
	// 新建文件类型
	newly_file_type: function (that) {
		var _type = parseInt($(that).attr('data-type')),
			_active = $('.ace_catalogue .ace_catalogue_list .has-children .file_fold.bg'),
			_group = parseInt(_active.attr('data-group')),
			_path = _active.parent().attr('data-menu-path'),
			_this = this;
		switch (_type) {
			case 0: //刷新目录
				_active.next().empty();
				_this.reader_file_dir_menu(
					{
						el: _active.next(),
						path: _path,
						group: parseInt(_active.attr('data-group')) + 1,
						is_empty: true,
					},
					function () {
						layer.msg('Refresh successfully', { icon: 1 });
					}
				);
				break;
			case 1: //打开文件
				_this.menu_path = _path;
				_this.reader_file_dir_menu({
					el: '.cd-accordion-menu',
					path: _this.menu_path,
					group: 1,
					is_empty: true,
				});
				break;
			case 2: //新建文件
			case 3:
				if (this.get_file_dir(_path, 1) != this.menu_path) {
					//判断当前文件上级是否为显示根目录
					this.reader_file_dir_menu({ el: _active, path: _path, group: _group + 1 }, function (res) {
						_this.newly_file_type_dom(_active, _group, _type == 2 ? 0 : 1);
					});
				} else {
					_this.newly_file_type_dom(_active, _group, _type == 2 ? 0 : 1);
				}
				break;
			case 4: //文件重命名
				var _types = _active.attr('data-file');
				if (_active.hasClass('active')) {
					layer.msg('The file is open and the name cannot be modified', { icon: 0 });
					return false;
				}
				_active.attr('data-edit', 2);
				_active.addClass('edit_file_group');
				_active.find('.file_title').hide();
				_active.find('.glyphicon').hide();
				_active.prepend(
					'<span class="file_input"><i class="' +
						(_types === 'Dir' ? 'folder' : _this.get_file_suffix(_active.find('.file_title span').html())) +
						'-icon"></i><input type="text" class="newly_file_input" value="' +
						_active.find('.file_title span').html() +
						'"><span class="glyphicon glyphicon-ok" aria-hidden="true"></span><span class="glyphicon glyphicon-remove" aria-hidden="true"></span>'
				);
				$('.file_fold .newly_file_input').width(
					$('.file_fold .newly_file_input').parent().parent().parent().width() - ($('.file_fold .newly_file_input').parent().parent().attr('data-group') * 15 - 5) - 20 - 30 - 53
				);
				$('.file_fold .newly_file_input').focus();
				break;
			case 5:
				GetFileBytes(_path);
				break;
			case 6:
				var is_files = _active.attr('data-file') === 'Files';
				layer.confirm(
					lan.get(is_files ? 'recycle_bin_confirm' : 'recycle_bin_confirm_dir', [_active.find('.file_title span').html()]),
					{ title: is_files ? lan.files.del_file : lan.files.del_dir, closeBtn: 2, icon: 3 },
					function (index) {
						_this[is_files ? 'del_file_req' : 'del_dir_req']({ path: _path }, function (res) {
							layer.msg(res.msg, { icon: res.status ? 1 : 2 });
							if (res.status) {
								if (_active.attr('data-group') != 1) _active.parent().parent().prev().addClass('bg');
								_this.reader_file_dir_menu(_this.refresh_config, function () {
									layer.msg(res.msg, { icon: 1 });
								});
							}
						});
					}
				);
				break;
		}
	},
	// 新建文件和文件夹
	newly_file_type_dom: function (_active, _group, _type, _val) {
		var _html = '',
			_this = this,
			_nextLength = _active.next(':not(.ace_catalogue_menu)').length;
		if (_nextLength > 0) {
			_active.next().show();
			_active.find('.glyphicon').removeClass('glyphicon-menu-right').addClass('glyphicon-menu-down');
		}
		_html +=
			'<li class="has-children children_' +
			(_group + 1) +
			'"><div class="file_fold edit_file_group group_' +
			(_group + 1) +
			'" data-group="' +
			(_group + 1) +
			'" data-edit="' +
			_type +
			'"><span class="file_input">';
		_html += '<i class="' + (_type == 0 ? 'folder' : _type == 1 ? 'text' : _this.get_file_suffix(_val || '')) + '-icon"></i>';
		_html += '<input type="text" class="newly_file_input" value="' + (_val != undefined ? _val : '') + '">';
		_html += '<span class="glyphicon glyphicon-ok" aria-hidden="true"></span><span class="glyphicon glyphicon-remove" aria-hidden="true"></span></span></div></li>';
		if (_nextLength > 0) {
			_active.next().prepend(_html);
		} else {
			_active.prepend(_html);
		}
		setTimeout(function () {
			$('.newly_file_input').focus();
		}, 100);
		$('.file_fold .newly_file_input').width(
			$('.file_fold .newly_file_input').parent().parent().parent().width() - ($('.file_fold .newly_file_input').parent().parent().attr('data-group') * 15 - 5) - 20 - 30 - 53
		);
		return false;
	},
	// newly_file_type_dom: function(_file_fold, _group, _type, _val) {
	//     var _html = '',
	//         _this = this;
	//     _file_fold.next().show();
	//     _file_fold.find('.glyphicon').removeClass('glyphicon-menu-right').addClass('glyphicon-menu-down');
	//     _html += '<li class="has-children children_' + (_group + 1) + '"><div class="file_fold edit_file_group group_' + (_group + 1) + '" data-group="' + (_group + 1) + '" data-edit="' + _type + '"><span class="file_input">';
	//     _html += '<i class="' + (_type == 0 ? 'folder' : (_type == 1 ? 'text' : (_this.get_file_suffix(_val)))) + '-icon"></i>'
	//     _html += '<input type="text" class="newly_file_input" value="' + (_val != undefined ? _val : '') + '">'
	//     _html += '<span class="glyphicon glyphicon-ok" aria-hidden="true"></span><span class="glyphicon glyphicon-remove" aria-hidden="true"></span></span></div></li>'
	//     _file_fold.next().prepend(_html);
	//     $('.file_fold .newly_file_input').width($('.file_fold .newly_file_input').parent().parent().parent().width() - ($('.file_fold .newly_file_input').parent().parent().attr('data-group') * 15 - 5) - 20 - 30 - 53);
	//     $('.newly_file_input').focus();
	// },
	// 通用重命名事件
	event_rename_currency: function (obj, that) {
		var _active = $('.ace_catalogue_list .has-children .file_fold.edit_file_group'),
			_this = this;
		this.rename_currency_req({ sfile: obj.sfile, dfile: obj.dfile }, function (res) {
			layer.msg(res.msg, { icon: res.status ? 1 : 2 });
			if (res.status) {
				_this.reader_file_dir_menu(_this.refresh_config, function () {
					layer.msg(res.msg, { icon: 1 });
				});
			} else {
				_active.find('.file_input').siblings().show();
				_active.find('.file_input').remove();
				_active.removeClass('edit_file_group').removeAttr('data-edit');
			}
		});
	},
	// 创建文件目录事件
	event_create_dir: function (obj, that) {
		var _this = this;
		this.create_dir_req({ path: obj.path }, function (res) {
			layer.msg(res.msg, { icon: res.status ? 1 : 2 });
			if (res.status) {
				_this.reader_file_dir_menu(_this.refresh_config, function () {
					layer.msg(res.msg, { icon: 1 });
				});
			}
		});
	},
	// 创建文件事件
	event_create_file: function (obj, that) {
		var _this = this;
		this.create_file_req({ path: obj.path }, function (res) {
			layer.msg(res.msg, { icon: res.status ? 1 : 2 });
			if (res.status) {
				_this.reader_file_dir_menu(_this.refresh_config, function () {
					layer.msg(res.msg, { icon: 1 });
					_this.openEditorView(obj.path);
				});
			}
		});
	},
	// 重命名请求
	rename_currency_req: function (obj, callback) {
		var loadT = layer.msg(lan.public.renaming_file, { time: 0, icon: 16, shade: [0.3, '#000'] });
		$.post(
			'/files?action=MvFile',
			{
				sfile: obj.sfile,
				dfile: obj.dfile,
				rename: 'true',
			},
			function (res) {
				layer.close(loadT);
				if (callback) callback(res);
			}
		);
	},
	// 创建文件事件
	create_file_req: function (obj, callback) {
		var loadT = layer.msg(lan.public.creating_file, { time: 0, icon: 16, shade: [0.3, '#000'] });
		$.post(
			'/files?action=CreateFile',
			{
				path: obj.path,
			},
			function (res) {
				layer.close(loadT);
				if (callback) callback(res);
			}
		);
	},
	// 创建目录请求
	create_dir_req: function (obj, callback) {
		var loadT = layer.msg(lan.public.creating_dir, { time: 0, icon: 16, shade: [0.3, '#000'] });
		$.post(
			'/files?action=CreateDir',
			{
				path: obj.path,
			},
			function (res) {
				layer.close(loadT);
				if (callback) callback(res);
			}
		);
	},
	// 删除文件请求
	del_file_req: function (obj, callback) {
		var loadT = layer.msg(lan.public.deleting_file, { time: 0, icon: 16, shade: [0.3, '#000'] });
		$.post(
			'/files?action=DeleteFile',
			{
				path: obj.path,
			},
			function (res) {
				layer.close(loadT);
				if (callback) callback(res);
			}
		);
	},
	// 删除目录请求
	del_dir_req: function (obj, callback) {
		var loadT = layer.msg(lan.public.deleting_dir, { time: 0, icon: 16, shade: [0.3, '#000'] });
		$.post(
			'/files?action=DeleteFile',
			{
				path: obj.path,
			},
			function (res) {
				layer.close(loadT);
				if (callback) callback(res);
			}
		);
	},
	// 临时文件保存
	auto_save_temp: function (obj, callback) {
		// var loadT = layer.msg('正在新建目录，请稍后...',{time: 0,icon: 16,shade: [0.3, '#000']});
		$.post(
			'/files?action=auto_save_temp',
			{
				filename: obj.filename,
				body: obj.body,
			},
			function (res) {
				layer.close(loadT);
				if (callback) callback(res);
			}
		);
	},
	// 获取临时文件内容
	get_auto_save_body: function (obj, callback) {
		var loadT = layer.msg(lan.public.get_autosave_file, { time: 0, icon: 16, shade: [0.3, '#000'] });
		$.post(
			'/files?action=get_auto_save_body',
			{
				filename: obj.filename,
			},
			function (res) {
				layer.close(loadT);
				if (callback) callback(res);
			}
		);
	},
	// 刷新菜单列表
	refresh_meun_list: function (el, callback) {
		var _active = $(el),
			_paths = _active.parent().attr('data-menu-path'),
			_group = parseInt(_active.attr('data-group')) + 1,
			_el = _active.next();
		_active.next().empty();
		if (_active.length === 0) {
			_el = $('.cd-accordion-menu');
			_paths = $('.ace_catalogue_title').attr('title');
			_group = 1;
			$('.cd-accordion-menu').empty();
		}
		this.reader_file_dir_menu(
			{
				el: _el,
				path: _paths,
				group: _group,
			},
			function (res) {
				if (callback) callback(res);
			}
		);
	},
	// 恢复历史文件事件
	event_ecovery_file: function (that) {
		var _path = $(that).attr('data-path'),
			_history = new Number($(that).attr('data-history')),
			_this = this;
		var loadT = layer.open({
			type: 1,
			//area: ['400px', '180px'],
			title: lan.public.restore_history_files,
			content:
				'<div class="ace-clear-form">\
				<div class="clear-icon"></div>\
				<div class="clear-title">' +
				lan.public.confirm_restore_file +
				'&nbsp<span class="size_ellipsis" style="max-width:150px;vertical-align: top;" title="' +
				bt.format_data(_history) +
				'">' +
				bt.format_data(_history) +
				'</span>?</div>\
				<div class="clear-tips">' +
				lan.public.confirm_restore_file1 +
				'</div>\
				<div class="ace-clear-btn" style="">\
					<button type="button" class="btn btn-sm btn-default" style="margin-right:10px;" data-type="1">' +
				lan.public.cancel +
				'</button>\
					<button type="button" class="btn btn-sm btn-success" data-type="0">' +
				lan.public.restore_history_files +
				'</button>\
				</div>\
			</div>',
			success: function (layero, index) {
				$('.ace-clear-btn .btn').click(function () {
					var _type = $(this).attr('data-type');
					switch (_type) {
						case '0':
							_this.recovery_file_history(
								{
									filename: _path,
									history: _history,
								},
								function (res) {
									layer.close(index);
									layer.msg(res.status ? lan.public.restore_history_files + ' ' + lan.public.success : lan.public.restore_history_files + ' ' + lan.public.fail, { icon: res.status ? 1 : 2 });
									if (res.status) {
										if (_this.editor['ace_editor_' + _this.ace_active].historys_file) {
											_this.removeEditor(_this.ace_active);
										}
										if ($('.ace_conter_menu>[title="' + _path + '"]').length > 0) {
											$('.ace_header .refreshs').click();
											layer.close(_this.layer_view);
										}
									}
								}
							);
							break;
						case '1':
							layer.close(index);
							break;
					}
				});
			},
		});
	},
	// 判断是否为历史文件
	is_file_history: function (_item) {
		if (_item.historys_file) {
			$('.ace_conter_tips').show();
			$('#ace_editor_' + _item.id).css('bottom', '50px');
			$('.ace_conter_tips .tips').html(
				lan.public.read_only_file +
					_item.path +
					', ' +
					lan.public.history_v +
					' [ ' +
					bt.format_data(new Number(_item.historys_active)) +
					' ]<a href="javascript:;" class="ml35 btlink" style="margin-left:35px" data-path="' +
					_item.path +
					'" data-history="' +
					_item.historys_active +
					'">' +
					lan.public.restore_history +
					'</a>'
			);
		} else {
			$('.ace_conter_tips').hide();
		}
	},
	// 判断文件是否打开
	is_file_open: function (path, callabck) {
		var is_state = false;
		for (var i = 0; i < this.pathAarry.length; i++) {
			if (path === this.pathAarry[i]) is_state = true;
		}
		if (callabck) {
			callabck(is_state);
		} else {
			return is_state;
		}
	},
	// 恢复文件历史
	recovery_file_history: function (obj, callback) {
		var loadT = layer.msg(lan.public.recover_file, { time: 0, icon: 16, shade: [0.3, '#000'] });
		$.post(
			'/files?action=re_history',
			{
				filename: obj.filename,
				history: obj.history,
			},
			function (res) {
				layer.close(loadT);
				if (callback) callback(res);
			}
		);
	},
	// 获取文件列表
	get_file_dir_list: function (obj, callback) {
		var loadT = layer.msg(lan.public.get_file_contents, { time: 0, icon: 16, shade: [0.3, '#000'] }),
			_this = this;
		if (obj['p'] === undefined) obj['p'] = 1;
		if (obj['showRow'] === undefined) obj['showRow'] = 200;
		if (obj['sort'] === undefined) obj['sort'] = 'name';
		if (obj['reverse'] === undefined) obj['reverse'] = 'False';
		if (obj['search'] === undefined) obj['search'] = '';
		if (obj['all'] === undefined) obj['all'] = 'False';
		$.post('/files?action=GetDir&tojs=GetFiles', { p: obj.p, showRow: obj.showRow, sort: obj.sort, reverse: obj.reverse, path: obj.path, search: obj.search }, function (res) {
			layer.close(loadT);
			if (callback) callback(res);
		});
	},
	// 获取文件列表
	get_file_dir_list: function (obj, callback) {
		var loadT = layer.msg('Getting file content, please wait...', { time: 0, icon: 16, shade: [0.3, '#000'] }),
			_this = this;
		if (obj['p'] === undefined) obj['p'] = 1;
		if (obj['showRow'] === undefined) obj['showRow'] = 200;
		if (obj['sort'] === undefined) obj['sort'] = 'name';
		if (obj['reverse'] === undefined) obj['reverse'] = 'False';
		if (obj['search'] === undefined) obj['search'] = '';
		if (obj['all'] === undefined) obj['all'] = 'False';
		$.post('/files?action=GetDir&tojs=GetFiles', { p: obj.p, showRow: obj.showRow, sort: obj.sort, reverse: obj.reverse, path: obj.path, search: obj.search }, function (res) {
			layer.close(loadT);
			if (callback) callback(res);
		});
	},
	// 获取历史文件
	get_file_history: function (obj, callback) {
		var loadT = layer.msg(lan.public.get_file_history, { time: 0, icon: 16, shade: [0.3, '#000'] }),
			_this = this;
		$.post('/files?action=read_history', { filename: obj.filename, history: obj.history }, function (res) {
			layer.close(loadT);
			if (callback) callback(res);
		});
	},
	// 渲染文件列表
	reader_file_dir_menu: function (obj, callback) {
		var _path = getCookie('Path'),
			_this = this;
		if (obj === undefined) obj = {};
		if (obj['el'] === undefined) obj['el'] = '.cd-accordion-menu';
		if (obj['group'] === undefined) obj['group'] = 1;
		if (obj['p'] === undefined) obj['p'] = 1;
		if (obj['path'] === undefined) obj['path'] = _path;
		if (obj['is_empty'] === undefined) obj['is_empty'] = false;
		if (obj['search'] === undefined) obj['search'] = '';
		if (obj['all'] === undefined) obj['all'] = 'False';
		this.get_file_dir_list({ p: obj.p, path: obj.path, search: obj.search, all: obj.all }, function (res) {
			var _dir = res.DIR,
				_files = res.FILES,
				_dir_dom = '',
				_files_dom = '',
				_html = '';
			_this.menu_path = res.PATH;
			for (var i = 0; i < _dir.length; i++) {
				var _data = _dir[i].split(';');
				if (_data[0] === '__pycache__') continue;
				_dir_dom +=
					'<li class="has-children children_' +
					obj.group +
					'" title="' +
					(obj.path + '/' + _data[0]) +
					'" data-menu-path="' +
					(obj.path + '/' + _data[0]) +
					'" data-size="' +
					_data[1] +
					'">\
					<div class="file_fold group_' +
					obj.group +
					'" data-group="' +
					obj.group +
					'" data-file="Dir">\
						<span class="glyphicon glyphicon-menu-right"></span>\
						<span class="file_title"><i class="folder-icon"></i><span>' +
					_data[0] +
					'</span></span>\
					</div>\
					<ul data-group=""></ul>\
					<span class="has_children_separator"></span>\
				</li>';
			}
			for (var j = 0; j < _files.length; j++) {
				var _data = _files[j].split(';');
				if (_data[0].indexOf('.pyc') !== -1) continue;
				_files_dom +=
					'<li class="has-children" title="' +
					(obj.path + '/' + _data[0]) +
					'" data-menu-path="' +
					(obj.path + '/' + _data[0]) +
					'" data-size="' +
					_data[1] +
					'" data-suffix="' +
					_this.get_file_suffix(_data[0]) +
					'">\
					<div class="file_fold  group_' +
					obj.group +
					'" data-group="' +
					obj.group +
					'" data-file="Files">\
						<span class="file_title"><i class="' +
					_this.get_file_suffix(_data[0]) +
					'-icon"></i><span>' +
					_data[0] +
					'</span></span>\
					</div>\
				</li>';
			}
			// if (res.PATH !== '/' && obj['group'] === 1) {
			//     _html = '<li class="has-children upper_level" data-menu-path="' + _this.get_file_dir(res.PATH, 1) + '"><span>'+lan.public.up_level+'</span></li>'
			//     $('.upper_level').attr('data-menu-path', _this.get_file_dir(res.PATH, 1));
			//     $('.ace_catalogue_title').html(lan.public.dir + ': ' + res.PATH).attr('title', res.PATH);
			// }
			if (res.PATH !== '/' && obj['group'] === 1) {
				$('.upper_level').attr('data-menu-path', _this.get_file_dir(res.PATH, 1));
				$('.ace_catalogue_title')
					.html(lan.public.dir + ': ' + res.PATH)
					.attr('title', res.PATH);
				$('.upper_level').html('<i class="glyphicon glyphicon-share-alt" aria-hidden="true"></i>Back');
			} else if (res.PATH === '/') {
				$('.upper_level').html('<i class="glyphicon glyphicon-hdd" aria-hidden="true"></i>Root');
			}
			if (obj.is_empty) $(obj.el).empty();
			$(obj.el).append(_html + _dir_dom + _files_dom);
			if (callback) callback(res);
		});
	},
	// 获取文件目录位置
	get_file_dir: function (path, num) {
		var _arry = path.split('/');
		if (path === '/') return '/';
		_arry.splice(-1, num);
		return _arry == '' ? '/' : _arry.join('/');
	},
	// 获取文件全称
	get_file_suffix: function (fileName) {
		var filenames = fileName.match(/\.([0-9A-z]*)$/);
		filenames = filenames == null ? 'text' : filenames[1];
		for (var name in this.supportedModes) {
			var data = this.supportedModes[name],
				suffixs = data[0].split('|'),
				filename = name.toLowerCase();
			for (var i = 0; i < suffixs.length; i++) {
				if (filenames == suffixs[i]) return filename;
			}
		}
		return 'text';
	},
	// // 设置编辑器视图
	// setEditorView: function() {
	//     // var page_height = $('.aceEditors').height();
	//     // var ace_header = $('.ace_header').height();
	//     // var ace_conter_menu = $('.ace_conter_menu').height();
	//     // var ace_conter_toolbar = $('.ace_conter_toolbar').height();
	//     // var _height = page_height - ace_header - ace_conter_menu;
	//     // //var _height= $('.aceEditors').height()-$('.ace_conter_menu').height()-$('.ace_header').height();
	//     // //$('.ace_conter_editor').height(_height);
	//     // $('.ace_conter_editor').height(_height);

	//     var page_height = $('.aceEditors').height();
	//     var aceEditorHeight = $('.aceEditors').height(),_this = this;
	//     var ace_conter_menu = $('.ace_conter_menu').height();
	//     var ace_conter_toolbar = $('.ace_conter_toolbar').height();
	//     var _height = page_height - ($('.pull-down .glyphicon').hasClass('glyphicon-menu-down')?35:0) - ace_conter_menu - ace_conter_toolbar - 42;
	//     $('.ace_conter_editor').height(_height);
	//     if(aceEditorHeight == $('.aceEditors').height()){
	//         if(_this.ace_active) _this.editor[_this.ace_active].ace.resize();
	//     }else {
	//         aceEditorHeight = $('.aceEditors').height();
	//     }
	//     $('.aceEditors').height();
	// },
	// 设置编辑器视图
	setEditorView: function () {
		var aceEditorHeight = $('.aceEditors').height(),
			_this = this;
		var autoAceHeight = setInterval(function () {
			var page_height = $('.aceEditors').height();
			var ace_conter_menu = $('.ace_conter_menu').height();
			var ace_conter_toolbar = $('.ace_conter_toolbar').height();
			var _height = page_height - ($('.pull-down .glyphicon').hasClass('glyphicon-menu-down') ? 35 : 0) - ace_conter_menu - ace_conter_toolbar - 42;
			$('.ace_conter_editor').height(_height);
			if (aceEditorHeight == $('.aceEditors').height()) {
				clearInterval(autoAceHeight);
				if (_this.ace_active != '') _this.editor['ace_editor_' + _this.ace_active].ace.resize();
			} else {
				aceEditorHeight = $('.aceEditors').height();
			}
		}, 200);
	},
	// 获取文件编码列表
	getEncodingList: function (type) {
		var _option = '';
		for (var i = 0; i < this.encodingList.length; i++) {
			var item = this.encodingList[i] == type.toUpperCase();
			_option +=
				'<li data- data-value="' +
				this.encodingList[i] +
				'" ' +
				(item ? 'class="active"' : '') +
				'>' +
				this.encodingList[i] +
				(item ? '<span class="icon"><i class="glyphicon glyphicon-ok" aria-hidden="true"></i></span>' : '') +
				'</li>';
		}
		$('.menu-encoding ul').html(_option);
	},
	// 获取文件关联列表
	getRelevanceList: function (fileName) {
		var _option = '',
			_top = 0,
			fileType = this.getFileType(fileName),
			_set_tops = 0;
		for (var name in this.supportedModes) {
			var data = this.supportedModes[name],
				item = name == fileType.name;
			_option +=
				'<li data-height="' +
				_top +
				'" data-rule="' +
				this.supportedModes[name] +
				'" data-value="' +
				name +
				'" ' +
				(item ? 'class="active"' : '') +
				'>' +
				(this.nameOverrides[name] || name) +
				(item ? '<span class="icon"><i class="glyphicon glyphicon-ok" aria-hidden="true"></i></span>' : '') +
				'</li>';
			if (item) _set_tops = _top;
			_top += 35;
		}
		$('.menu-files ul').html(_option);
		$('.menu-files ul').scrollTop(_set_tops);
	},
	// 搜索文件关联
	searchRelevance: function (search) {
		if (search == undefined) search = '';
		$('.menu-files ul li').each(function (index, el) {
			var val = $(this).attr('data-value').toLowerCase(),
				rule = $(this).attr('data-rule'),
				suffixs = rule.split('|'),
				_suffixs = false;
			search = search.toLowerCase();
			for (var i = 0; i < suffixs.length; i++) {
				if (suffixs[i].indexOf(search) > -1) _suffixs = true;
			}
			if (search == '') {
				$(this).removeAttr('style');
			} else {
				if (val.indexOf(search) == -1) {
					$(this).attr('style', 'display:none');
				} else {
					$(this).removeAttr('style');
				}
				if (_suffixs) $(this).removeAttr('style');
			}
		});
	},
	// 设置编码类型
	setEncodingType: function (encode) {
		this.getEncodingList('UTF-8');
		$('.menu-encoding ul li').click(function (e) {
			layer.msg(lan.public.set_file_encoding + ': ' + $(this).attr('data-value'));
			$(this).addClass('active').append('<span class="icon"><i class="glyphicon glyphicon-ok" aria-hidden="true"></i></span>').siblings().removeClass('active').find('span').remove();
		});
	},
	// 更新状态栏
	currentStatusBar: function (id) {
		var _editor = this.editor['ace_editor_' + id];
		$('.ace_conter_toolbar [data-type="history"]').html(lan.public.history_v + ': <i>' + (_editor.historys.length === 0 ? lan.public.empty : _editor.historys.length) + '</i>');
		$('.ace_conter_toolbar [data-type="path"]').html(lan.public.dir + ': <i title="' + _editor.path + '">' + _editor.path + '</i>');
		$('.ace_conter_toolbar [data-type="tab"]').html(_editor.softTabs ? lan.public.space + ': <i>' + _editor.tabSize + '</i>' : lan.public.tab_length + ': <i>' + _editor.tabSize + '</i>');
		$('.ace_conter_toolbar [data-type="encoding"]').html(lan.public.encoding + ': <i>' + _editor.encoding.toUpperCase() + '</i>');
		$('.ace_conter_toolbar [data-type="lang"]').html(lan.public.lan + ': <i>' + _editor.type + '</i>');
		$('.ace_conter_toolbar span').attr('data-id', id);
		$('.file_fold').removeClass('bg');
		$('[data-menu-path="' + aceEditor.editor['ace_editor_' + id].path + '"]')
			.find('.file_fold')
			.addClass('bg');
		if (_editor.historys_file) {
			$('.ace_conter_toolbar [data-type="history"]').hide();
		} else {
			$('.ace_conter_toolbar [data-type="history"]').show();
		}
		_editor.ace.resize();
	},
	// currentStatusBar: function(id) {
	//     var _item = this.editor['ace_editor_' + id];
	// 	if(_item == undefined){
	// 		this.removerStatusBar();
	// 		return false;
	// 	}
	//     $('.ace_conter_toolbar [data-type="cursor"]').html(lan.public.row + '<i class="cursor-row">1</i>,'+ lan.public.column +'<i class="cursor-line">0</i>');
	//     $('.ace_conter_toolbar [data-type="history"]').html(lan.public.history_v + ': <i>' + (_item.historys.length === 0 ? lan.public.empty : _item.historys.length) + '</i>');
	//     $('.ace_conter_toolbar [data-type="path"]').html(lan.public.dir + ': <i title="' + _item.path + '">' + _item.path + '</i>');
	//     $('.ace_conter_toolbar [data-type="tab"]').html(_item.softTabs ? lan.public.space + ': <i>' + _item.tabSize + '</i>' : lan.public.tab_length + ': <i>' + _item.tabSize + '</i>');
	//     $('.ace_conter_toolbar [data-type="encoding"]').html(lan.public.encoding + ': <i>' + _item.encoding.toUpperCase() + '</i>');
	//     $('.ace_conter_toolbar [data-type="lang"]').html(lan.public.lan + ': <i>' + _item.type + '</i>');
	//     $('.ace_conter_toolbar span').attr('data-id', id);
	//     $('.file_fold').removeClass('bg');
	//     $('[data-menu-path="' + (_item.path) + '"]').find('.file_fold').addClass('bg');
	//     if (_item.historys_file) {
	//         $('.ace_conter_toolbar [data-type="history"]').hide();
	//     } else {
	//         $('.ace_conter_toolbar [data-type="history"]').show();
	//     }
	//     _item.ace.resize();
	// },
	// 清除状态栏
	removerStatusBar: function () {
		$('.ace_conter_toolbar [data-type="history"]').html('');
		$('.ace_conter_toolbar [data-type="path"]').html('');
		$('.ace_conter_toolbar [data-type="tab"]').html('');
		$('.ace_conter_toolbar [data-type="cursor"]').html('');
		$('.ace_conter_toolbar [data-type="encoding"]').html('');
		$('.ace_conter_toolbar [data-type="lang"]').html('');
	},
	// 创建ACE编辑器-对象
	creationEditor: function (obj, callabck) {
		var _this = this;
		$('#ace_editor_' + obj.id).text(obj.data || '');
		$('.ace_conter_editor .ace_editors').css('fontSize', _this.aceConfig.aceEditor.fontSize);
		if (this.editor == null) this.editor = {};
		this.editor['ace_editor_' + obj.id] = {
			ace: ace.edit('ace_editor_' + obj.id, {
				theme: 'ace/theme/' + _this.aceConfig.aceEditor.editorTheme, //主题
				mode: 'ace/mode/' + (obj.fileName != undefined ? obj.mode : 'text'), // 语言类型
				wrap: _this.aceConfig.aceEditor.wrap,
				showInvisibles: _this.aceConfig.aceEditor.showInvisibles,
				showPrintMargin: false,
				enableBasicAutocompletion: true,
				enableSnippets: _this.aceConfig.aceEditor.enableSnippets,
				enableLiveAutocompletion: _this.aceConfig.aceEditor.enableLiveAutocompletion,
				useSoftTabs: _this.aceConfig.aceEditor.useSoftTabs,
				tabSize: _this.aceConfig.aceEditor.tabSize,
				keyboardHandler: 'sublime',
				readOnly: obj.readOnly === undefined ? false : obj.readOnly,
			}), //ACE编辑器对象
			id: obj.id,
			wrap: _this.aceConfig.aceEditor.wrap, //是否换行
			path: obj.path,
			tabSize: _this.aceConfig.aceEditor.tabSize,
			softTabs: _this.aceConfig.aceEditor.useSoftTabs,
			fileName: obj.fileName,
			enableSnippets: true, //是否代码提示
			encoding: obj.encoding != undefined ? obj.encoding : 'utf-8', //编码类型
			mode: obj.fileName != undefined ? obj.mode : 'text', //语言类型
			type: obj.type,
			fileType: 0, //文件状态
			historys: obj.historys,
			historys_file: obj.historys_file === undefined ? false : obj.historys_file,
			historys_active: obj.historys_active === '' ? false : obj.historys_active,
		};
		var ACE = this.editor['ace_editor_' + obj.id];
		ACE.ace.moveCursorTo(0, 0); //设置鼠标焦点
		ACE.ace.resize(); //设置自适应
		ACE.ace.commands.addCommand({
			name: lan.public.save,
			bindKey: {
				win: 'Ctrl-S',
				mac: 'Command-S',
			},
			exec: function (editor) {
				_this.saveFileMethod(ACE);
			},
			readOnly: false, // 如果不需要使用只读模式，这里设置false
		});

		// 获取光标位置
		ACE.ace.getSession().selection.on('changeCursor', function (e) {
			var _cursor = ACE.ace.selection.getCursor();
			$('[data-type="cursor"]').html(lan.public.row + '<i class="cursor-row">' + (_cursor.row + 1) + '</i>,' + lan.public.column + '<i class="cursor-line">' + _cursor.column + '</i>');
			//$('.ace_toolbar_menu').hide();
		});

		// 触发修改内容
		ACE.ace.getSession().on('change', function (editor) {
			$('.item_tab_' + ACE.id + ' .icon-tool')
				.addClass('glyphicon-exclamation-sign')
				.removeClass('glyphicon-remove')
				.attr('data-file-state', '1');
			ACE.fileType = 1;
			$('.ace_toolbar_menu').hide();
		});
		this.currentStatusBar(ACE.id);
		this.is_file_history(ACE);
	},
	// 保存文件方法
	saveFileMethod: function (ACE) {
		this.saveFileBody(
			{
				path: ACE.path,
				data: ACE.ace.getValue(),
				encoding: ACE.encoding,
			},
			function (res) {
				layer.msg(res.msg, { icon: res.status ? 1 : 2 });
				ACE.fileType = 0;
				$('.item_tab_' + ACE.id + ' .icon-tool')
					.attr('data-file-state', '0')
					.removeClass('glyphicon-exclamation-sign')
					.addClass('glyphicon-remove');
			}
		);
	},
	// 获取文件模型
	getFileType: function (fileName) {
		var filenames = fileName.match(/\.([0-9A-z]*)$/);
		filenames = filenames == null ? 'text' : filenames[1];
		for (var name in this.supportedModes) {
			var data = this.supportedModes[name],
				suffixs = data[0].split('|'),
				filename = name.toLowerCase();
			for (var i = 0; i < suffixs.length; i++) {
				if (filenames == suffixs[i]) {
					return { name: name, mode: filename };
				}
			}
		}
		return { name: 'Text', mode: 'text' };
	},
	// 新建编辑器视图-方法
	// addEditorView: function() {
	//     var _index = this.editorLength,
	//         _id = bt.get_random(8);
	//     $('.ace_conter_menu .item').removeClass('active');
	//     $('.ace_conter_editor .ace_editors').removeClass('active');
	//     $('.ace_conter_menu .ace_editor_add').before('<div class="item active item_tab_' + _id + '" data-type="text" data-id="' + _id + '" data-index="' + _index + '">\
	// 		<span class="icon_file"><i class="fa fa-code" aria-hidden="true"></i></span>\
	// 		<span>Untitled-' + _index + '</span>\
	// 		<i class="fa fa-circle icon-tool" aria-hidden="true" data-file-state="1" data-title="Untitled-' + _index + '"></i>\
	// 	</div>');
	//     $('.ace_conter_editor').append('<div id="ace_editor_' + _id + '" class="ace_editors active"></div>');
	//     $('#ace_editor_' + _id).siblings().removeClass('active');
	//     this.creationEditor({ id: _id });
	//     this.editorLength = this.editorLength + 1;
	// },
	addEditorView: function (type, conifg) {
		if (type == undefined) type = 0;
		var _index = this.editorLength,
			_id = bt.get_random(8);
		$('.ace_conter_menu .item').removeClass('active');
		$('.ace_conter_editor .ace_editors').removeClass('active');
		$('.ace_conter_menu').append(
			'<li class="item active item_tab_' +
				_id +
				'" data-type="shortcutKeys" data-id="' +
				_id +
				'" >\
			<div class="ace_item_box">\
				<span class="icon_file"><i class="text-icon"></i></span>\
				<span>' +
				(type ? conifg.title : 'Untitled-' + _index) +
				'</span>\
				<i class="glyphicon icon-tool glyphicon-remove" aria-hidden="true" data-file-state="0" data-title="' +
				(type ? conifg.title : 'Untitled-' + _index) +
				'"></i>\
			</div>\
		</li>'
		);
		$('#ace_editor_' + _id)
			.siblings()
			.removeClass('active');
		$('.ace_conter_editor').append('<div id="ace_editor_' + _id + '" class="ace_editors active">' + (type ? aceShortcutKeys.innerHTML : '') + '</div>');
		switch (type) {
			case 0:
				this.creationEditor({ id: _id });
				this.editorLength = this.editorLength + 1;
				break;
			case 1:
				this.removerStatusBar();
				this.editorLength = this.editorLength + 1;
				break;
		}
	},
	// 删除编辑器视图-方法
	removeEditor: function (id) {
		if (id == undefined) id = this.ace_active;
		if ($('.item_tab_' + id).next('.item').length != 0 && this.editorLength != 1) {
			$('.item_tab_' + id)
				.next('.item')
				.click();
		} else if ($('.item_tab_' + id).prev('.item').length != 0 && this.editorLength != 1) {
			$('.item_tab_' + id)
				.prev('.item')
				.click();
		}
		$('.item_tab_' + id).remove();
		$('#ace_editor_' + id).remove();
		this.editorLength--;
		if (this.editor['ace_editor_' + id] == undefined) return false;
		for (var i = 0; i < this.pathAarry.length; i++) {
			if (this.pathAarry[i] == this.editor['ace_editor_' + id].path) {
				this.pathAarry.splice(i, 1);
			}
		}
		if (!this.editor['ace_editor_' + id].historys_file)
			$('[data-menu-path="' + this.editor['ace_editor_' + id].path + '"]')
				.find('.file_fold')
				.removeClass('active bg');
		delete this.editor['ace_editor_' + id];
		if (this.editorLength === 0) {
			this.ace_active = '';
			this.pathAarry = [];
			this.removerStatusBar();
		} else {
			this.currentStatusBar(this.ace_active);
		}
		if (this.ace_active != '') this.is_file_history(this.editor['ace_editor_' + this.ace_active]);
	},
	// 打开历史文件文件-方法
	openHistoryEditorView: function (obj, callback) {
		// 文件类型（type，列如：JavaScript） 、文件模型（mode，列如：text）、文件标识（id,列如：x8AmsnYn）、文件编号（index,列如：0）、文件路径 (path，列如：/www/root/)
		var _this = this,
			path = obj.filename,
			paths = path.split('/'),
			_fileName = paths[paths.length - 1],
			_fileType = this.getFileType(_fileName),
			_type = _fileType.name,
			_mode = _fileType.mode,
			_id = bt.get_random(8),
			_index = this.editorLength;
		this.get_file_history({ filename: obj.filename, history: obj.history }, function (res) {
			_this.pathAarry.push(path);
			$('.ace_conter_menu .item').removeClass('active');
			$('.ace_conter_editor .ace_editors').removeClass('active');
			$('.ace_conter_menu').append(
				'<li class="item active item_tab_' +
					_id +
					'" title="' +
					path +
					'" data-type="' +
					_type +
					'" data-mode="' +
					_mode +
					'" data-id="' +
					_id +
					'" data-fileName="' +
					_fileName +
					'">' +
					'<div class="ace_item_box">' +
					'<span class="icon_file"><img src="/static/img/ico-history.png"></span><span title="' +
					path +
					lan.public.history_v +
					' [ ' +
					bt.format_data(obj.history) +
					' ]' +
					'">' +
					_fileName +
					'</span>' +
					'<i class="glyphicon glyphicon-remove icon-tool" aria-hidden="true" data-file-state="0" data-title="' +
					_fileName +
					'"></i>' +
					'</div>' +
					'</li>'
			);
			$('.ace_conter_editor').append('<div id="ace_editor_' + _id + '" class="ace_editors active"></div>');
			$('[data-paths="' + path + '"]')
				.find('.file_fold')
				.addClass('active bg');
			_this.ace_active = _id;
			_this.editorLength = _this.editorLength + 1;
			_this.creationEditor({
				id: _id,
				fileName: _fileName,
				path: path,
				mode: _mode,
				encoding: res.encoding,
				data: res.data,
				type: _type,
				historys: res.historys,
				readOnly: true,
				historys_file: true,
				historys_active: obj.history,
			});
			if (callback) callback(res);
		});
	},
	// 打开编辑器文件-方法
	// openEditorView: function(path, callback) {
	//     if (path == undefined) return false;
	//     // 文件类型（type，列如：JavaScript） 、文件模型（mode，列如：text）、文件标识（id,列如：x8AmsnYn）、文件编号（index,列如：0）、文件路径 (path，列如：/www/root/)
	//     var _this = this,
	//         paths = path.split('/'),
	//         _fileName = paths[paths.length - 1],
	//         _fileType = this.getFileType(_fileName),
	//         _type = _fileType.name,
	//         _mode = _fileType.mode,
	//         _id = bt.get_random(8),
	//         _index = this.editorLength;
	//     _this.is_file_open(path, function(is_state) {
	//         if (is_state) {
	//             $('.ace_conter_menu').find('[title="' + path + '"]').click();
	//         } else {
	//             _this.getFileBody({ path: path }, function(res) {
	//                 _this.pathAarry.push(path);
	//                 $('.ace_conter_menu .item').removeClass('active');
	//                 $('.ace_conter_editor .ace_editors').removeClass('active');
	//                 $('.ace_conter_menu .ace_editor_add').before('<div class="item active item_tab_' + _id + '" title="' + path + '" data-type="' + _type + '" data-mode="' + _mode + '" data-id="' + _id + '" data-index="' + _index + '" data-fileName="' + _fileName + '">\
	// 	    			<span class="icon_file"><i class="' + _mode + '-icon"></i></span><span title="' + path + '">' + _fileName + '</span>\
	// 	    			<i class="glyphicon glyphicon-remove icon-tool" aria-hidden="true" data-file-state="0" data-title="' + _fileName + '"></i>\
	// 	    		</div>');
	//                 $('.ace_conter_editor').append('<div id="ace_editor_' + _id + '" class="ace_editors active"></div>');
	//                 $('[data-menu-path="' + path + '"]').find('.file_fold').addClass('active bg');
	//                 _this.ace_active = _id;
	//                 _this.editorLength = _this.editorLength + 1;
	//                 _this.creationEditor({ id: _id, fileName: _fileName, path: path, mode: _mode, encoding: res.encoding, data: res.data, type: _type, historys: res.historys });
	//                 if (callback) callback(res);
	//             });
	//         }
	//     });
	//     $('.ace_toolbar_menu').hide();
	// },
	openEditorView: function (path, callback) {
		// 最小化后，再点文件编辑，还原编辑器窗口
		if (aceEditor.editorStatus === -1) $('.layui-layer-maxmin').click();
		if (path == undefined) return false;
		// 文件类型（type，列如：JavaScript） 、文件模型（mode，列如：text）、文件标识（id,列如：x8AmsnYn）、文件编号（index,列如：0）、文件路径 (path，列如：/www/root/)
		var _this = this,
			paths = path.split('/'),
			_fileName = paths[paths.length - 1],
			_fileType = this.getFileType(_fileName),
			_type = _fileType.name,
			_mode = _fileType.mode,
			_id = bt.get_random(8),
			_index = this.editorLength;
		_this.is_file_open(path, function (is_state) {
			if (is_state) {
				$('.ace_conter_menu')
					.find('[title="' + path + '"]')
					.click();
			} else {
				_this.getFileBody({ path: path }, function (res) {
					_this.pathAarry.push(path);
					$('.ace_conter_menu .item').removeClass('active');
					$('.ace_conter_editor .ace_editors').removeClass('active');
					$('.ace_conter_menu').append(
						'<li class="item active item_tab_' +
							_id +
							'" title="' +
							path +
							'" data-type="' +
							_type +
							'" data-mode="' +
							_mode +
							'" data-id="' +
							_id +
							'" data-fileName="' +
							_fileName +
							'">' +
							'<div class="ace_item_box">' +
							'<span class="icon_file"><i class="' +
							_mode +
							'-icon"></i></span><span title="' +
							path +
							'">' +
							_fileName +
							'</span>' +
							'<i class="glyphicon glyphicon-remove icon-tool" aria-hidden="true" data-file-state="0" data-title="' +
							_fileName +
							'"></i>' +
							'</div>' +
							'</li>'
					);
					$('.ace_conter_editor').append('<div id="ace_editor_' + _id + '" class="ace_editors active" style="font-size:' + aceEditor.aceConfig.aceEditor.fontSize + 'px"></div>');
					$('[data-menu-path="' + path + '"]')
						.find('.file_fold')
						.addClass('active bg');
					_this.ace_active = _id;
					_this.editorLength = _this.editorLength + 1;
					_this.creationEditor({ id: _id, fileName: _fileName, path: path, mode: _mode, encoding: res.encoding, data: res.data, type: _type, historys: res.historys });
					if (callback) callback(res);
				});
			}
		});
		$('.ace_toolbar_menu').hide();
	},
	// 获取收藏夹列表-方法
	getFavoriteList: function () {},
	// 获取文件列表-请求
	getFileList: function () {},
	// 获取文件内容-请求
	getFileBody: function (obj, callback) {
		var loadT = layer.msg(lan.public.get_file_contents, { time: 0, icon: 16, shade: [0.3, '#000'] }),
			_this = this;
		$.post('/files?action=GetFileBody', 'path=' + encodeURIComponent(obj.path), function (res) {
			layer.close(loadT);
			if (!res.status) {
				if (_this.editorLength == 0) layer.closeAll();
				layer.msg(res.msg, { icon: 2 });

				return false;
			} else {
				if (!aceEditor.isAceView) {
					var _path = obj.path.split('/');
					layer.msg(lan.public.opend_file + ' [' + _path[_path.length - 1] + ']');
				}
			}
			if (callback) callback(res);
		});
	},
	// 保存文件内容-请求
	// saveFileBody: function(obj, callback) {
	//     var loadT = layer.msg(lan.public.save_file_content, { time: 0, icon: 16, shade: [0.3, '#000'] });
	//     $.post("/files?action=SaveFileBody", {
	//         data:obj.data,
	//         encoding:obj.encoding.toLowerCase(),
	//         path:obj.path
	//     }, function(res) {
	//         layer.close(loadT);
	//         if (callback) callback(res)
	//     });
	// },
	saveFileBody: function (obj, success, error) {
		$.ajax({
			type: 'post',
			url: '/files?action=SaveFileBody',
			timeout: 7000, //设置保存超时时间
			data: {
				data: obj.data,
				encoding: obj.encoding.toLowerCase(),
				path: obj.path,
			},
			success: function (rdata) {
				if (rdata.status) {
					if (success) success(rdata);
				} else {
					if (error) error(rdata);
				}
				if (!obj.tips) layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
			},
			error: function (err) {
				if (error) error(err);
			},
		});
	},
	saveAceConfig: function (data, callback) {
		var loadT = layer.msg(lan.public.save_ace_config, { time: 0, icon: 16, shade: [0.3, '#000'] }),
			_this = this;
		this.saveFileBody(
			{
				path: '/www/server/panel/BTPanel/static/ace/ace.editor.config.json',
				data: JSON.stringify(data),
				encoding: 'utf-8',
				tips: true,
			},
			function (rdata) {
				layer.close(loadT);
				_this.setStorage('aceConfig', JSON.stringify(data));
				if (callback) callback(rdata);
			}
		);
	},
	// 获取配置文件
	getEditorConfig: function (callback) {
		var loadT = layer.msg(lan.public.get_ace_config, { time: 0, icon: 16, shade: [0.3, '#000'] }),
			_this = this;
		this.getFileBody({ path: '/www/server/panel/BTPanel/static/ace/ace.editor.config.json' }, function (rdata) {
			layer.close(loadT);
			_this.setStorage('aceConfig', JSON.stringify(rdata.data));
			if (callback) callback(JSON.parse(rdata.data));
		});
	},
	getAceConfig: function (callback) {
		var loadT = layer.msg(lan.public.get_ace_config, { time: 0, icon: 16, shade: [0.3, '#000'] }),
			_this = this;
		this.getFileBody({ path: '/www/server/panel/BTPanel/static/ace/ace.editor.config.json' }, function (rdata) {
			layer.close(loadT);
			_this.setStorage('aceConfig', JSON.stringify(rdata.data));
			if (callback) callback(JSON.parse(rdata.data));
		});
	},
	// 递归保存文件
	saveAllFileBody: function (arry, num, callabck) {
		var _this = this;
		if (typeof num == 'function') {
			callabck = num;
			num = 0;
		} else if (typeof num == 'undefined') {
			num = 0;
		}
		if (num == arry.length) {
			if (callabck) callabck();
			layer.msg(lan.public.save_all, { icon: 1 });
			return false;
		}
		aceEditor.saveFileBody(
			{
				path: arry[num].path,
				data: arry[num].data,
				encoding: arry[num].encoding,
			},
			function () {
				num = num + 1;
				aceEditor.saveAllFileBody(arry, num, callabck);
			}
		);
	},
};

function openEditorView(type, path) {
	var paths = path.split('/'),
		_fileName = paths[paths.length - 1],
		_aceTmplate = document.getElementById('aceTmplate').innerHTML;
	_aceTmplate = _aceTmplate.replace(/\<\\\/script\>/g, '</script>');
	if (aceEditor.editor !== null) {
		if (aceEditor.isAceView == false) {
			aceEditor.isAceView = true;
			$('.aceEditors .layui-layer-max').click();
		}
		aceEditor.openEditorView(path);
		return false;
	}
	var r = layer.open({
		type: 1,
		maxmin: true,
		shade: false,
		area: ['80%', '80%'],
		title: lan.public.online_text_editor,
		skin: 'aceEditors',
		zIndex: 19999,
		content: _aceTmplate,
		success: function (layero, index) {
			function set_edit_file() {
				// aceEditor.layer_view = index;
				aceEditor.ace_active = '';
				aceEditor.eventEditor();
				$('#ace_conter').addClass(aceEditor.editorTheme);
				ace.require('/ace/ext/language_tools');
				ace.config.set('modePath', '/static/ace');
				ace.config.set('workerPath', '/static/ace');
				ace.config.set('themePath', '/static/ace');
				aceEditor.openEditorView(path);
				var _left = parseInt($(layero).css('left')),
					_top = parseInt($(layero).css('top'));
				_left < 0 ? $(layero).css('left', Math.abs(_left)) : $(layero).css('left', _left);
				_top < 0 ? $(layero).css('top', Math.abs(_top)) : $(layero).css('top', _top);
				// $('.aceEditors .layui-layer-min').click(function(e) {
				//     aceEditor.isAceView = false;
				//     setTimeout(function() {
				//         var _id = $('.ace_conter_menu .active').attr('data-id');
				//         aceEditor.editor['ace_editor_' + _id].ace.resize();
				//     }, 105);
				// });
				// $('.aceEditors .layui-layer-max').click(function(e) {
				//     setTimeout(function() {
				//         aceEditor.setEditorView();
				//         var _id = $('.ace_conter_menu .active').attr('data-id');
				//         aceEditor.editor['ace_editor_' + _id].ace.resize();
				//     }, 105);
				// });
				$('.aceEditors .layui-layer-min').click(function (e) {
					aceEditor.setEditorView();
				});
				$('.aceEditors .layui-layer-max').click(function (e) {
					aceEditor.setEditorView();
				});
			}
			var aceConfig = aceEditor.getStorage('aceConfig');
			if (aceConfig == null) {
				// 获取编辑器配置
				aceEditor.getAceConfig(function (res) {
					aceEditor.aceConfig = res; // 赋值配置参数
					set_edit_file();
				});
			} else {
				aceEditor.aceConfig = JSON.parse(aceConfig);
				typeof aceEditor.aceConfig == 'string' ? (aceEditor.aceConfig = JSON.parse(aceEditor.aceConfig)) : '';
				set_edit_file();
			}
		},
		cancel: function () {
			for (var item in aceEditor.editor) {
				if (aceEditor.editor[item].fileType == 1) {
					layer.open({
						type: 1,
						area: ['400px', '180px'],
						title: lan.public.save_tips,
						content:
							'\
							<div class="ace-clear-form">\
								<div class="clear-icon"></div>\
								<div class="clear-title">' +
							lan.public.save_tips1 +
							'</div>\
								<div class="clear-tips">' +
							lan.public.save_tips2 +
							'</div>\
								<div class="ace-clear-btn" style="">\
									<button type="button" class="btn btn-sm btn-default" style="float:left" data-type="2">' +
							lan.public.dont_save +
							'</button>\
									<button type="button" class="btn btn-sm btn-default" style="margin-right:10px;" data-type="1">' +
							lan.public.cancel +
							'</button>\
									<button type="button" class="btn btn-sm btn-success" data-type="0">' +
							lan.public.save +
							'</button>\
								</div>\
							</div>',
						success: function (layers, indexs) {
							$('.ace-clear-btn button').click(function () {
								var _type = $(this).attr('data-type');
								switch (_type) {
									case '2':
										aceEditor.editor = null;
										layer.closeAll();
										break;
									case '1':
										layer.close(indexs);
										break;
									case '0':
										var _arry = [],
											editor = aceEditor['editor'];
										for (var item in editor) {
											_arry.push({
												path: editor[item]['path'],
												data: editor[item]['ace'].getValue(),
												encoding: editor[item]['encoding'],
											});
										}
										aceEditor.saveAllFileBody(_arry, function () {
											$('.ace_conter_menu>.item').each(function (el, indexx) {
												var _id = $(this).attr('data-id');
												$(this).find('i').removeClass('glyphicon-exclamation-sign').addClass('glyphicon-remove').attr('data-file-state', '0');
												aceEditor.editor['ace_editor_' + _id].fileType = 0;
											});
											aceEditor.editor = null;
											aceEditor.pathAarry = [];
											layer.closeAll();
										});
										break;
								}
							});
						},
					});
					return false;
				}
			}
		},
		full: function (layero, index) {
			//最大化
			aceEditor.editorStatus = 1;
		},
		min: function (layero, index) {
			//最小化
			aceEditor.editorStatus = -1;
		},
		restore: function (layero, index) {
			//还原
			aceEditor.editorStatus = 0;
		},
		end: function () {
			aceEditor.ace_active = '';
			aceEditor.editor = null;
			aceEditor.pathAarry = [];
			aceEditor.menu_path = '';
		},
	});
}

/**
 * AES加密
 * @param {string} s_text 等待加密的字符串
 * @param {string} s_key 16位密钥
 * @param {array} ctx 可选，默认为 { mode: CryptoJS.mode.ECB,padding: CryptoJS.pad.ZeroPadding }
 * @return {string}
 */
function aes_encrypt(s_text, s_key, ctx) {
	if (ctx == undefined) ctx = { mode: CryptoJS.mode.ECB, padding: CryptoJS.pad.ZeroPadding };
	var key = CryptoJS.enc.Utf8.parse(s_key);
	var encrypt_data = CryptoJS.AES.encrypt(s_text, key, ctx);
	return encrypt_data.toString();
}

/**
 * AES解密
 * @param {string} s_text 等待解密的密文
 * @param {string} s_key 16位密钥
 * @param {array} ctx 可选，默认为 { mode: CryptoJS.mode.ECB,padding: CryptoJS.pad.ZeroPadding }
 * @return {string}
 */
function aes_decrypt(s_text, s_key, ctx) {
	if (ctx == undefined) ctx = { mode: CryptoJS.mode.ECB, padding: CryptoJS.pad.ZeroPadding };
	var key = CryptoJS.enc.Utf8.parse(s_key);
	var decrypt_data = CryptoJS.AES.decrypt(s_text, key, ctx);
	return decrypt_data.toString(CryptoJS.enc.Utf8);
}

/**
 * ajax内容解密
 * @param {string} data 加密的响应数据
 * @param {string} stype ajax中定义的数据类型
 * @return {string} 解密后的响应数据
 */
function ajax_decrypt(data, stype) {
	if (!data) return data;
	if (data.substring(0, 6) == 'BT-CRT') {
		var token = $('#request_token_head').attr('token');
		var pwd = token.substring(0, 8) + token.substring(40, 48);
		data = aes_decrypt(data.substring(6), pwd);
		if (stype == undefined) {
			stype = '';
		}
		if (stype.toLowerCase() != 'json') {
			data = JSON.parse(data);
		}
	}
	return data;
}
/**
 * 格式化form_data数据，并加密
 * @param {string} form_data 加密前的form_data数据
 * @return {string} 加密后的form_data数据
 */
function format_form_data(form_data) {
	var data_tmp = form_data.split('&');
	var form_info = {};
	var token = $('#request_token_head').attr('token');
	if (!token) return form_data;
	var pwd = token.substring(0, 8) + token.substring(40, 48);
	for (var i = 0; i < data_tmp.length; i++) {
		var tmp = data_tmp[i].split('=');
		if (tmp.length < 2) continue;
		// if(!tmp[1]) continue;
		var val = decodeURIComponent(tmp[1].replace(/\+/g, '%20'));
		if (val.length > 3) {
			form_info[tmp[0]] = 'BT-CRT' + aes_encrypt(val, pwd);
		} else {
			form_info[tmp[0]] = val;
		}
	}
	return $.param(form_info);
}

function ajax_encrypt(request) {
	if (!this.type || !this.data || !this.contentType) return;
	if ($('#panel_debug').attr('data') == 'True') return;
	if ($('#panel_debug').attr('data-pyversion') == '2') return;
	if (this.type == 'POST' && this.data.length > 1) {
		this.data = format_form_data(this.data);
	}
}

// function ajaxSetup() {
//     var my_headers = {};
//     var request_token_ele = document.getElementById("request_token_head");
//     if (request_token_ele) {
//         var request_token = request_token_ele.getAttribute('token');
//         if (request_token) {
//             my_headers['x-http-token'] = request_token
//         }
//     }
//     request_token_cookie = getCookie('request_token');
//     if (request_token_cookie) {
//         my_headers['x-cookie-token'] = request_token_cookie
//     }
//
//     if (my_headers) {
//         $.ajaxSetup({
// 			headers: my_headers,
// 			// dataFilter: ajax_decrypt,
// 			// beforeSend: ajax_encrypt
// 		});
//     }
// }
function ajaxSetup() {
	var my_headers = {};
	var request_token_ele = document.getElementById('request_token_head');
	if (request_token_ele) {
		var request_token = request_token_ele.getAttribute('token');
		if (request_token) {
			my_headers['x-http-token'] = request_token;
		}
	}
	request_token_cookie = getCookie('request_token');
	if (request_token_cookie) {
		my_headers['x-cookie-token'] = request_token_cookie;
	}

	if (my_headers) {
		$.ajaxSetup({
			headers: my_headers,
			error: function (jqXHR, textStatus, errorThrown) {
				if (!jqXHR.responseText) return;
				if (typeof String.prototype.trim === 'undefined') {
					String.prototype.trim = function () {
						return String(this).replace(/^\s+|\s+$/g, '');
					};
				}

				error_key = 'We need to make sure this has a favicon so that the debugger does';
				error_find = jqXHR.responseText.indexOf(error_key);
				if (jqXHR.status == 500 && (jqXHR.responseText.indexOf('An error occurred while the panel was running') != -1 || error_find != -1)) {
					// if(jqXHR.responseText.indexOf('请先绑定宝塔帐号!') != -1){
					// 	bt.pub.bind_btname(function(){
					// 		window.location.reload();
					// 	});
					// 	return;
					// }
					if (error_find != -1) {
						var error_body = jqXHR.responseText.split('<!--')[2].replace('-->', '');
						var tmp = error_body.split('During handling of the above exception, another exception occurred:');
						error_body = tmp[tmp.length - 1];
						var error_msg =
							'<div>\
						<h3 style="margin-bottom: 10px;">出错了，面板运行时发生错误！</h3>\
						<pre style="height:635px;word-wrap: break-word;white-space: pre-wrap;margin: 0 0 0px">' +
							error_body.trim() +
							'</pre>\
						<ul class="help-info-text">\
							<li style="list-style: none;"><b>很抱歉，面板运行时意外发生错误，请尝试按以下顺序尝试解除此错误：</b></li>\
							<li style="list-style: none;">1、在[首页]右上角点击修复面板，并退出面板重新登录。</li>\
							<li style="list-style: none;">2、如上述尝试未能解除此错误，请截图此窗口到宝塔论坛发贴寻求帮助, 论坛地址：<a class="btlink" href="https://www.bt.cn/bbs" target="_blank">https://www.bt.cn/bbs</a></li>\
						</ul>\
					</div>';
					} else {
						var error_msg = jqXHR.responseText;
					}
					$('.layui-layer-padding').parents('.layer-anim').remove();
					$('.layui-layer-shade').remove();
					setTimeout(function () {
						layer.open({
							title: false,
							content: error_msg,
							closeBtn: 2,
							area: ['1000px', '800px'],
							btn: false,
							shadeClose: false,
							shade: 0.3,
							success: function () {
								$('pre').scrollTop(100000000000);
							},
						});
					}, 100);
				}
			},
			// dataFilter: ajax_decrypt,
			// beforeSend: ajax_encrypt
		});
	}
}
ajaxSetup();

function RandomStrPwd(b) {
	b = b || 32;
	var c = 'AaBbCcDdEeFfGHhiJjKkLMmNnPpRSrTsWtXwYxZyz2345678';
	var a = c.length;
	var d = '';
	for (i = 0; i < b; i++) {
		d += c.charAt(Math.floor(Math.random() * a));
	}
	return d;
}

function repeatPwd(a) {
	$('#MyPassword').val(RandomStrPwd(a));
}

function refresh() {
	window.location.reload();
}

function GetBakPost(b) {
	$('.baktext').hide().prev().show();
	var c = $('.baktext').attr('data-id');
	var a = $('.baktext').val();
	if (a == '') {
		a = lan.bt.empty;
	}
	setWebPs(b, c, a);
	$("a[data-id='" + c + "']").html(a);
	$('.baktext').remove();
}

function setWebPs(b, e, a) {
	var d = layer.load({
		shade: true,
		shadeClose: false,
	});
	var c = 'ps=' + a;
	$.post('/data?action=setPs', 'table=' + b + '&id=' + e + '&' + c, function (f) {
		if (f == true) {
			if (b == 'sites') {
				getWeb(1);
			} else {
				if (b == 'ftps') {
					getFtp(1);
				} else {
					getData(1);
				}
			}
			layer.closeAll();
			layer.msg(lan.public.edit_ok, {
				icon: 1,
			});
		} else {
			layer.msg(lan.public.edit_err, {
				icon: 2,
			});
			layer.closeAll();
		}
	});
}

$('.menu-icon').click(function () {
	$('.sidebar-scroll').toggleClass('sidebar-close');
	$('.main-content').toggleClass('main-content-open');
	if ($('.sidebar-close')) {
		$('.sub-menu').find('.sub').css('display', 'none');
	}
});
var Upload, percentage;

Date.prototype.format = function (b) {
	var c = {
		'M+': this.getMonth() + 1,
		'd+': this.getDate(),
		'h+': this.getHours(),
		'm+': this.getMinutes(),
		's+': this.getSeconds(),
		'q+': Math.floor((this.getMonth() + 3) / 3),
		S: this.getMilliseconds(),
	};
	if (/(y+)/.test(b)) {
		b = b.replace(RegExp.$1, (this.getFullYear() + '').substr(4 - RegExp.$1.length));
	}
	for (var a in c) {
		if (new RegExp('(' + a + ')').test(b)) {
			b = b.replace(RegExp.$1, RegExp.$1.length == 1 ? c[a] : ('00' + c[a]).substr(('' + c[a]).length));
		}
	}
	return b;
};

function getLocalTime(a) {
	a = a.toString();
	if (a.length > 10) {
		a = a.substring(0, 10);
	}
	return new Date(parseInt(a) * 1000).format('yyyy/MM/dd hh:mm:ss');
}

function ToSize(a) {
	var d = [' B', ' KB', ' MB', ' GB', ' TB', ' PB'];
	var e = 1024;
	for (var b = 0; b < d.length; b++) {
		if (a < e) {
			return (b == 0 ? a : a.toFixed(2)) + d[b];
		}
		a /= e;
	}
}

function ChangePath(d) {
	setCookie('SetId', d);
	setCookie('SetName', '');
	var c = layer.open({
		type: 1,
		area: '680px',
		title: lan.bt.dir,
		closeBtn: 2,
		shift: 5,
		shadeClose: false,
		content:
			"<div class='changepath'><div class='path-top'><button type='button' class='btn btn-default btn-sm' onclick='BackFile()'><span class='glyphicon glyphicon-share-alt'></span> " +
			lan.public.return +
			"</button><div class='place' id='PathPlace'>" +
			lan.bt.path +
			"：<span></span></div></div><div class='path-con'><div class='path-con-left'><dl><dt id='changecomlist' onclick='BackMyComputer()'>" +
			lan.bt.comp +
			"</dt></dl></div><div class='path-con-right'><ul class='default' id='computerDefautl'></ul><div class='file-list divtable'><table class='table table-hover' style='border:0 none'><thead><tr class='file-list-head'><th width='40%'>" +
			lan.bt.filename +
			"</th><th width='20%'>" +
			lan.bt.etime +
			"</th><th width='10%'>" +
			lan.bt.access +
			"</th><th width='10%'>" +
			lan.bt.own +
			"</th><th width='10%'></th></tr></thead><tbody id='tbody' class='list-list'></tbody></table></div></div></div></div><div class='getfile-btn' style='margin-top:0'><button type='button' class='btn btn-default btn-sm pull-left' onclick='CreateFolder()'>" +
			lan.bt.adddir +
			"</button><button type='button' class='btn btn-danger btn-sm mr5' onclick=\"layer.close(getCookie('ChangePath'))\">" +
			lan.public.close +
			"</button> <button type='button' class='btn btn-success btn-sm' onclick='GetfilePath()'>" +
			lan.bt.path_ok +
			'</button></div>',
	});
	setCookie('ChangePath', c);
	var b = $('#' + d).val();
	tmp = b.split('.');
	if (tmp[tmp.length - 1] == 'gz') {
		tmp = b.split('/');
		b = '';
		for (var a = 0; a < tmp.length - 1; a++) {
			b += '/' + tmp[a];
		}
		setCookie('SetName', tmp[tmp.length - 1]);
	}
	b = b.replace(/\/\//g, '/');
	GetDiskList(b);
	ActiveDisk();
}

function GetDiskList(b) {
	var d = '';
	var a = '';
	var c = 'path=' + b + '&disk=True';
	$.post('/files?action=GetDir', c, function (h) {
		if (h.status == false) {
			layer.close(layer.index);
			layer.msg(h.msg, { icon: 2 });
			return false;
		}
		if (h.DISK != undefined) {
			for (var f = 0; f < h.DISK.length; f++) {
				a += '<dd onclick="GetDiskList(\'' + h.DISK[f].path + "')\"><span class='glyphicon glyphicon-hdd'></span>&nbsp;" + h.DISK[f].path + '</dd>';
			}
			$('#changecomlist').html(a);
		}
		for (var f = 0; f < h.DIR.length; f++) {
			var g = h.DIR[f].split(';');
			var e = g[0];
			if (e.length > 20) {
				e = e.substring(0, 20) + '...';
			}
			if (isChineseChar(e)) {
				if (e.length > 10) {
					e = e.substring(0, 10) + '...';
				}
			}
			d +=
				'<tr><td onclick="GetDiskList(\'' +
				h.PATH +
				'/' +
				g[0] +
				"')\" title='" +
				g[0] +
				"'><span class='glyphicon glyphicon-folder-open'></span>" +
				e +
				'</td><td>' +
				getLocalTime(g[2]) +
				'</td><td>' +
				g[3] +
				'</td><td>' +
				g[4] +
				"</td><td><span class='delfile-btn' onclick=\"NewDelFile('" +
				h.PATH +
				'/' +
				g[0] +
				'\')">X</span></td></tr>';
		}
		if (h.FILES != null && h.FILES != '') {
			for (var f = 0; f < h.FILES.length; f++) {
				var g = h.FILES[f].split(';');
				var e = g[0];
				if (e.length > 20) {
					e = e.substring(0, 20) + '...';
				}
				if (isChineseChar(e)) {
					if (e.length > 10) {
						e = e.substring(0, 10) + '...';
					}
				}
				d += "<tr><td title='" + g[0] + "'><span class='glyphicon glyphicon-file'></span>" + e + '</td><td>' + getLocalTime(g[2]) + '</td><td>' + g[3] + '</td><td>' + g[4] + '</td><td></td></tr>';
			}
		}
		$('.default').hide();
		$('.file-list').show();
		$('#tbody').html(d);
		if (h.PATH.substr(h.PATH.length - 1, 1) != '/') {
			h.PATH += '/';
		}
		$('#PathPlace').find('span').html(h.PATH);
		ActiveDisk();
		return;
	});
}

function CreateFolder() {
	var a =
		"<tr><td colspan='2'><span class='glyphicon glyphicon-folder-open'></span> <input id='newFolderName' class='newFolderName' type='text' value=''></td><td colspan='3'><button id='nameOk' type='button' class='btn btn-success btn-sm'>" +
		lan.public.ok +
		"</button>&nbsp;&nbsp;<button id='nameNOk' type='button' class='btn btn-default btn-sm'>" +
		lan.public.cancel +
		'</button></td></tr>';
	if ($('#tbody tr').length == 0) {
		$('#tbody').append(a);
	} else {
		$('#tbody tr:first-child').before(a);
	}
	$('.newFolderName').focus();
	$('#nameOk').click(function () {
		var c = $('#newFolderName').val();
		var b = $('#PathPlace').find('span').text();
		newTxt = b.replace(new RegExp(/(\/\/)/g), '/') + c;
		var d = 'path=' + newTxt;
		$.post('/files?action=CreateDir', d, function (e) {
			if (e.status == true) {
				layer.msg(e.msg, {
					icon: 1,
				});
			} else {
				layer.msg(e.msg, {
					icon: 2,
				});
			}
			GetDiskList(b);
		});
	});
	$('#nameNOk').click(function () {
		$(this).parents('tr').remove();
	});
}

function NewDelFile(c) {
	var a = $('#PathPlace').find('span').text();
	newTxt = c.replace(new RegExp(/(\/\/)/g), '/');
	var b = 'path=' + newTxt + '&empty=True';
	$.post('/files?action=DeleteDir', b, function (d) {
		if (d.status == true) {
			layer.msg(d.msg, {
				icon: 1,
			});
		} else {
			layer.msg(d.msg, {
				icon: 2,
			});
		}
		GetDiskList(a);
	});
}

function ActiveDisk() {
	var a = $('#PathPlace').find('span').text().substring(0, 1);
	switch (a) {
		case 'C':
			$('.path-con-left dd:nth-of-type(1)').css('background', '#eee').siblings().removeAttr('style');
			break;
		case 'D':
			$('.path-con-left dd:nth-of-type(2)').css('background', '#eee').siblings().removeAttr('style');
			break;
		case 'E':
			$('.path-con-left dd:nth-of-type(3)').css('background', '#eee').siblings().removeAttr('style');
			break;
		case 'F':
			$('.path-con-left dd:nth-of-type(4)').css('background', '#eee').siblings().removeAttr('style');
			break;
		case 'G':
			$('.path-con-left dd:nth-of-type(5)').css('background', '#eee').siblings().removeAttr('style');
			break;
		case 'H':
			$('.path-con-left dd:nth-of-type(6)').css('background', '#eee').siblings().removeAttr('style');
			break;
		default:
			$('.path-con-left dd').removeAttr('style');
	}
}

function BackMyComputer() {
	$('.default').show();
	$('.file-list').hide();
	$('#PathPlace').find('span').html('');
	ActiveDisk();
}

function BackFile() {
	var c = $('#PathPlace').find('span').text();
	if (c.substr(c.length - 1, 1) == '/') {
		c = c.substr(0, c.length - 1);
	}
	var d = c.split('/');
	var a = '';
	if (d.length > 1) {
		var e = d.length - 1;
		for (var b = 0; b < e; b++) {
			a += d[b] + '/';
		}
		GetDiskList(a.replace('//', '/'));
	} else {
		a = d[0];
	}
	if (d.length == 1) {
	}
}

function GetfilePath() {
	var a = $('#PathPlace').find('span').text();
	a = a.replace(new RegExp(/(\\)/g), '/');
	setCookie('path_dir_change', a);
	$('#' + getCookie('SetId')).val(a + getCookie('SetName'));
	layer.close(getCookie('ChangePath'));
}

function setCookie(a, c) {
	var b = 30;
	var d = new Date();
	d.setTime(d.getTime() + b * 24 * 60 * 60 * 1000);
	document.cookie = a + '=' + escape(c) + ';expires=' + d.toGMTString();
}

function getCookie(b) {
	var a,
		c = new RegExp('(^| )' + b + '=([^;]*)(;|$)');
	if ((a = document.cookie.match(c))) {
		return unescape(a[2]);
	} else {
		return null;
	}
}

function aotuHeight() {
	var a = $('body').height() - 50;
	$('.main-content').css('min-height', a);
}
$(function () {
	aotuHeight();
});
$(window).resize(function () {
	aotuHeight();
});

function showHidePwd() {
	var a = 'glyphicon-eye-open',
		b = 'glyphicon-eye-close';
	$('.pw-ico').click(function () {
		var g = $(this).attr('class'),
			e = $(this).prev();
		if (g.indexOf(a) > 0) {
			var h = e.attr('data-pw');
			$(this).removeClass(a).addClass(b);
			e.text(h);
		} else {
			$(this).removeClass(b).addClass(a);
			e.text('**********');
		}
		var d = $(this).next().position().left;
		var f = $(this).next().position().top;
		var c = $(this).next().width();
		$(this)
			.next()
			.next()
			.css({
				left: d + c + 'px',
				top: f + 'px',
			});
	});
}

function openPath(a) {
	setCookie('Path', a);
	window.location.href = '/files';
}

function OnlineEditFile(k, f) {
	if (k != 0) {
		var l = $('#PathPlace input').val();
		var h = encodeURIComponent($('#textBody').val());
		var a = $('select[name=encoding]').val();
		var loadT = layer.msg(lan.bt.save_file, {
			icon: 16,
			time: 0,
		});
		$.post('/files?action=SaveFileBody', 'data=' + h + '&path=' + encodeURIComponent(f) + '&encoding=' + a, function (m) {
			if (k == 1) {
				layer.close(loadT);
			}
			layer.msg(m.msg, {
				icon: m.status ? 1 : 2,
			});
		});
		return;
	}
	var e = layer.msg(lan.bt.read_file, {
		icon: 16,
		time: 0,
	});
	var g = f.split('.');
	var b = g[g.length - 1];
	var d;
	switch (b) {
		case 'html':
			var j = {
				name: 'htmlmixed',
				scriptTypes: [
					{
						matches: /\/x-handlebars-template|\/x-mustache/i,
						mode: null,
					},
					{
						matches: /(text|application)\/(x-)?vb(a|script)/i,
						mode: 'vbscript',
					},
				],
			};
			d = j;
			break;
		case 'htm':
			var j = {
				name: 'htmlmixed',
				scriptTypes: [
					{
						matches: /\/x-handlebars-template|\/x-mustache/i,
						mode: null,
					},
					{
						matches: /(text|application)\/(x-)?vb(a|script)/i,
						mode: 'vbscript',
					},
				],
			};
			d = j;
			break;
		case 'js':
			d = 'text/javascript';
			break;
		case 'json':
			d = 'application/ld+json';
			break;
		case 'css':
			d = 'text/css';
			break;
		case 'php':
			d = 'application/x-httpd-php';
			break;
		case 'tpl':
			d = 'application/x-httpd-php';
			break;
		case 'xml':
			d = 'application/xml';
			break;
		case 'sql':
			d = 'text/x-sql';
			break;
		case 'conf':
			d = 'text/x-nginx-conf';
			break;
		default:
			var j = {
				name: 'htmlmixed',
				scriptTypes: [
					{
						matches: /\/x-handlebars-template|\/x-mustache/i,
						mode: null,
					},
					{
						matches: /(text|application)\/(x-)?vb(a|script)/i,
						mode: 'vbscript',
					},
				],
			};
			d = j;
	}
	$.post('/files?action=GetFileBody', 'path=' + encodeURIComponent(f), function (s) {
		if (s.status === false) {
			layer.msg(s.msg, { icon: 5 });
			return;
		}
		layer.close(e);
		var u = ['utf-8', 'GBK', 'GB2312', 'BIG5'];
		var n = '';
		var m = '';
		var o = '';
		for (var p = 0; p < u.length; p++) {
			m = s.encoding == u[p] ? 'selected' : '';
			n += '<option value="' + u[p] + '" ' + m + '>' + u[p] + '</option>';
		}
		var r = layer.open({
			type: 1,
			shift: 5,
			closeBtn: 2,
			area: ['90%', '90%'],
			title: lan.bt.edit_title + '[' + f + ']',
			content:
				'<form class="bt-form pd20 pb70"><div class="line"><p style="color:red;margin-bottom:10px">' +
				lan.bt.edit_ps +
				'			<select class="bt-input-text" name="encoding" style="width: 74px;position: absolute;top: 31px;right: 19px;height: 22px;z-index: 9999;border-radius: 0;">' +
				n +
				'</select></p><textarea class="mCustomScrollbar bt-input-text" id="textBody" style="width:100%;margin:0 auto;line-height: 1.8;position: relative;top: 10px;" value="" />			</div>			<div class="bt-form-submit-btn" style="position:absolute; bottom:0; width:100%">			<button type="button" class="btn btn-danger btn-sm btn-editor-close">' +
				lan.public.close +
				'</button>			<button id="OnlineEditFileBtn" type="button" class="btn btn-success btn-sm">' +
				lan.public.save +
				'</button>			</div>			</form>',
		});
		$('#textBody').text(s.data);
		var q = $(window).height() * 0.9;
		$('#textBody').height(q - 160);
		var t = CodeMirror.fromTextArea(document.getElementById('textBody'), {
			extraKeys: {
				'Ctrl-F': 'findPersistent',
				'Ctrl-H': 'replaceAll',
				'Ctrl-S': function () {
					$('#textBody').text(t.getValue());
					OnlineEditFile(2, f);
				},
			},
			mode: d,
			lineNumbers: true,
			matchBrackets: true,
			matchtags: true,
			autoMatchParens: true,
		});
		t.focus();
		t.setSize('auto', q - 150);
		$('#OnlineEditFileBtn').click(function () {
			$('#textBody').text(t.getValue());
			OnlineEditFile(1, f);
		});
		$('.btn-editor-close').click(function () {
			layer.close(r);
		});
	});
}

function ServiceAdmin(a, b) {
	if (!isNaN(a)) {
		a = 'php-fpm-' + a;
	}
	a = a.replace('_soft', '');
	var c = 'name=' + a + '&type=' + b;
	var d = '';

	switch (b) {
		case 'stop':
			d = lan.bt.stop;
			break;
		case 'start':
			d = lan.bt.start;
			break;
		case 'restart':
			d = lan.bt.restart;
			break;
		case 'reload':
			d = lan.bt.reload;
			break;
	}
	layer.confirm(
		lan.get('service_confirm', [d, a]),
		{
			icon: 3,
			closeBtn: 2,
		},
		function () {
			var e = layer.msg(lan.get('service_the', [d, a]), {
				icon: 16,
				time: 0,
			});
			$.post('/system?action=ServiceAdmin', c, function (g) {
				layer.close(e);

				var f = g.status ? lan.get('service_ok', [a, d]) : lan.get('service_err', [a, d]);
				layer.msg(f, {
					icon: g.status ? 1 : 2,
				});
				if (b != 'reload' && g.status == true) {
					setTimeout(function () {
						window.location.reload();
					}, 1000);
				}
				if (!g.status) {
					layer.msg(g.msg, {
						icon: 2,
						time: 0,
						shade: 0.3,
						shadeClose: true,
					});
				}
			}).error(function () {
				layer.close(e);
				layer.msg(lan.public.success, {
					icon: 1,
				});
			});
		}
	);
}

function GetConfigFile(a) {
	var b = '';
	switch (a) {
		case 'mysql':
			b = '/etc/my.cnf';
			break;
		case 'nginx':
			b = '/www/server/nginx/conf/nginx.conf';
			break;
		case 'pure-ftpd':
			b = '/www/server/pure-ftpd/etc/pure-ftpd.conf';
			break;
		case 'apache':
			b = '/www/server/apache/conf/httpd.conf';
			break;
		case 'tomcat':
			b = '/www/server/tomcat/conf/server.xml';
			break;
		default:
			b = '/www/server/php/' + a + '/etc/php.ini';
			break;
	}
	OnlineEditFile(0, b);
}

function GetPHPStatus(a) {
	if (a == '52') {
		layer.msg(lan.bt.php_status_err, {
			icon: 2,
		});
		return;
	}
	$.post('/ajax?action=GetPHPStatus', 'version=' + a, function (b) {
		layer.open({
			type: 1,
			area: '400',
			title: lan.bt.php_status_title,
			closeBtn: 2,
			shift: 5,
			shadeClose: true,
			content:
				"<div style='margin:15px;'><table class='table table-hover table-bordered'>						<tr><th>" +
				lan.bt.php_pool +
				'</th><td>' +
				b.pool +
				'</td></tr>						<tr><th>' +
				lan.bt.php_manager +
				'</th><td>' +
				(b['process manager'] == 'dynamic' ? lan.bt.dynamic : lan.bt.static) +
				'</td></tr>						<tr><th>' +
				lan.bt.php_start +
				'</th><td>' +
				b['start time'] +
				'</td></tr>						<tr><th>' +
				lan.bt.php_accepted +
				'</th><td>' +
				b['accepted conn'] +
				'</td></tr>						<tr><th>' +
				lan.bt.php_queue +
				'</th><td>' +
				b['listen queue'] +
				'</td></tr>						<tr><th>' +
				lan.bt.php_max_queue +
				'</th><td>' +
				b['max listen queue'] +
				'</td></tr>						<tr><th>' +
				lan.bt.php_len_queue +
				'</th><td>' +
				b['listen queue len'] +
				'</td></tr>						<tr><th>' +
				lan.bt.php_idle +
				'</th><td>' +
				b['idle processes'] +
				'</td></tr>						<tr><th>' +
				lan.bt.php_active +
				'</th><td>' +
				b['active processes'] +
				'</td></tr>						<tr><th>' +
				lan.bt.php_total +
				'</th><td>' +
				b['total processes'] +
				'</td></tr>						<tr><th>' +
				lan.bt.php_max_active +
				'</th><td>' +
				b['max active processes'] +
				'</td></tr>						<tr><th>' +
				lan.bt.php_max_children +
				'</th><td>' +
				b['max children reached'] +
				'</td></tr>						<tr><th>' +
				lan.bt.php_slow +
				'</th><td>' +
				b['slow requests'] +
				'</td></tr>					 </table></div>',
		});
	});
}

function GetNginxStatus() {
	$.post('/ajax?action=GetNginxStatus', '', function (a) {
		layer.open({
			type: 1,
			area: '400',
			title: lan.bt.nginx_title,
			closeBtn: 2,
			shift: 5,
			shadeClose: true,
			content:
				"<div style='margin:15px;'><table class='table table-hover table-bordered'>						<tr><th>" +
				lan.bt.nginx_active +
				'</th><td>' +
				a.active +
				'</td></tr>						<tr><th>' +
				lan.bt.nginx_accepts +
				'</th><td>' +
				a.accepts +
				'</td></tr>						<tr><th>' +
				lan.bt.nginx_handled +
				'</th><td>' +
				a.handled +
				'</td></tr>						<tr><th>' +
				lan.bt.nginx_requests +
				'</th><td>' +
				a.requests +
				'</td></tr>						<tr><th>' +
				lan.bt.nginx_reading +
				'</th><td>' +
				a.Reading +
				'</td></tr>						<tr><th>' +
				lan.bt.nginx_writing +
				'</th><td>' +
				a.Writing +
				'</td></tr>						<tr><th>' +
				lan.bt.nginx_waiting +
				'</th><td>' +
				a.Waiting +
				'</td></tr>					 </table></div>',
		});
	});
}

function divcenter() {
	$('.layui-layer').css('position', 'absolute');
	var c = $(window).width();
	var b = $('.layui-layer').outerWidth();
	var g = $(window).height();
	var f = $('.layui-layer').outerHeight();
	var a = (c - b) / 2;
	var e = (g - f) / 2 > 0 ? (g - f) / 2 : 10;
	var d = $('.layui-layer').offset().left - $('.layui-layer').position().left;
	var h = $('.layui-layer').offset().top - $('.layui-layer').position().top;
	a = a + $(window).scrollLeft() - d;
	e = e + $(window).scrollTop() - h;
	$('.layui-layer').css('left', a + 'px');
	$('.layui-layer').css('top', e + 'px');
}

function btcopy(password) {
	$('#bt_copys').attr('data-clipboard-text', password);
	$('#bt_copys').click();
}

function loadScript(arry, param, callback) {
	var ready = 0;
	if (typeof param === 'function') callback = param;
	for (var i = 0; i < arry.length; i++) {
		if (!Array.isArray(bt['loadScript'])) {
			bt['loadScript'] = [];
		}
		if (!is_file_existence(arry[i], true)) {
			if (arry.length - 1 === i && callback) callback();
			continue;
		}
		var script = document.createElement('script'),
			_arry_split = arry[i].split('/');
		script.type = 'text/javascript';
		if (typeof callback != 'undefined') {
			if (script.readyState) {
				(function (i) {
					script.onreadystatechange = function () {
						console.log(arry[i]);
						if (script.readyState == 'loaded' || script.readyState == 'complete') {
							script.onreadystatechange = null;
							bt['loadScript'].push(arry[i]);
							ready++;
						}
					};
				})(i);
			} else {
				(function (i) {
					script.onload = function () {
						if (!bt['loadScript']) bt['loadScript'] = [];
						bt['loadScript'].push(arry[i]);
						ready++;
					};
				})(i);
			}
		}
		script.src = arry[i];
		document.body.appendChild(script);
	}
	var time = setInterval(function () {
		if (ready === arry.length) {
			clearTimeout(time);
			callback();
		}
	}, 10);
}
// 判断文件是否插入
function is_file_existence(name, type) {
	var arry = type ? bt.loadScript : bt.loadLink;
	for (var i = 0; i < arry.length; i++) {
		if (arry[i] === name) return false;
	}
	return true;
}
// var clipboard = new ClipboardJS('#bt_copys');
// clipboard.on('success', function(e) {
//     layer.msg(lan.public.cp_success, { icon: 1 });
// });

// clipboard.on('error', function(e) {
//     layer.msg(lan.index.cp_fail, { icon: 2 });
// });

function isChineseChar(b) {
	var a = /[\u4E00-\u9FA5\uF900-\uFA2D]/;
	return a.test(b);
}

function SafeMessage(j, h, g, f) {
	if (f == undefined) {
		f = '';
	}
	var d = Math.round(Math.random() * 9 + 1);
	var c = Math.round(Math.random() * 9 + 1);
	var e = '';
	e = d + c;
	sumtext = d + ' + ' + c;
	setCookie('vcodesum', e);
	var mess = layer.open({
		type: 1,
		title: j,
		area: '350px',
		closeBtn: 2,
		shadeClose: true,
		content:
			"<div class='bt-form webDelete pd20 pb70'><p>" +
			h +
			'</p>' +
			f +
			"<div class='vcode'>" +
			lan.bt.cal_msg +
			"<span class='text'>" +
			sumtext +
			"</span>=<input type='number' id='vcodeResult' value=''></div><div class='bt-form-submit-btn'><button type='button' class='btn btn-danger btn-sm bt-cancel'>" +
			lan.public.cancel +
			"</button> <button type='button' id='toSubmit' class='btn btn-success btn-sm' >" +
			lan.public.ok +
			'</button></div></div>',
	});
	$('#vcodeResult')
		.focus()
		.keyup(function (a) {
			if (a.keyCode == 13) {
				$('#toSubmit').click();
			}
		});
	$('.bt-cancel').click(function () {
		layer.close(mess);
	});
	$('#toSubmit').click(function () {
		var a = $('#vcodeResult').val().replace(/ /g, '');
		if (a == undefined || a == '') {
			layer.msg(lan.public.input_calc_result);
			return;
		}
		if (a != getCookie('vcodesum')) {
			layer.msg(lan.public.input_calc_result);
			return;
		}
		layer.close(mess);
		g();
	});
}

$(function () {
	$('.fb-ico')
		.hover(
			function () {
				$('.fb-text').css({
					left: '36px',
					top: 0,
					width: '80px',
				});
			},
			function () {
				$('.fb-text').css({
					left: 0,
					width: '36px',
				});
			}
		)
		.click(function () {
			$('.fb-text').css({
				left: 0,
				width: '36px',
			});
			$('.zun-feedback-suggestion').show();
		});
	$('.fb-close').click(function () {
		$('.zun-feedback-suggestion').hide();
	});
	$('.fb-attitudes li').click(function () {
		$(this).addClass('fb-selected').siblings().removeClass('fb-selected');
	});
});
$('#dologin').click(function () {
	layer.confirm(
		lan.bt.loginout,
		{
			icon: 3,
			closeBtn: 2,
			title: 'Logout',
		},
		function () {
			window.location.href = '/login?dologin=True';
		}
	);
	return false;
});

function setPassword(a) {
	if (a == 1) {
		p1 = $('#p1').val();
		p2 = $('#p2').val();
		if (p1 == '' || p1.length < 8) {
			layer.msg(lan.bt.pass_err_len, {
				icon: 2,
			});
			return;
		}

		//准备弱口令匹配元素
		var checks = ['admin888', '123123123', '12345678', '45678910', '87654321', 'asdfghjkl', 'password', 'qwerqwer'];
		pchecks = 'abcdefghijklmnopqrstuvwxyz1234567890';
		for (var i = 0; i < pchecks.length; i++) {
			checks.push(pchecks[i] + pchecks[i] + pchecks[i] + pchecks[i] + pchecks[i] + pchecks[i] + pchecks[i] + pchecks[i]);
		}

		//检查弱口令
		cps = p1.toLowerCase();
		var isError = '';
		for (var i = 0; i < checks.length; i++) {
			if (cps == checks[i]) {
				isError += '[' + checks[i] + '] ';
			}
		}

		if (isError != '') {
			layer.msg(lan.bt.pass_err + isError, { icon: 5 });
			return;
		}

		if (p1 != p2) {
			layer.msg(lan.bt.pass_err_re, {
				icon: 2,
			});
			return;
		}

		var pdata = {
			password1: rsa.encrypt_public(p1),
			password2: rsa.encrypt_public(p2),
		};

		$.post('/config?action=setPassword', pdata, function (b) {
			if (b.status) {
				layer.closeAll();
				layer.msg(b.msg, {
					icon: 1,
				});
			} else {
				layer.msg(b.msg, {
					icon: 2,
				});
			}
		});
		return;
	}
	layer.open({
		type: 1,
		area: '290px',
		title: lan.bt.pass_title,
		closeBtn: 2,
		shift: 5,
		shadeClose: false,
		content:
			"<div class='bt-form pd20 pb70'><div class='line'><span class='tname'>" +
			lan.public.pass +
			"</span><div class='info-r'><input class='bt-input-text' type='text' name='password1' id='p1' value='' placeholder='" +
			lan.bt.pass_new_title +
			"' style='width:100%'/></div></div><div class='line'><span class='tname'>" +
			lan.bt.pass_re +
			"</span><div class='info-r'><input class='bt-input-text' type='text' name='password2' id='p2' value='' placeholder='" +
			lan.bt.pass_re_title +
			"' style='width:100%' /></div></div><div class='bt-form-submit-btn'><span style='float: left;' title='" +
			lan.bt.pass_rep +
			"' class='btn btn-default btn-sm' onclick='randPwd(10)'>" +
			lan.bt.pass_rep_btn +
			"</span><button type='button' class='btn btn-danger btn-sm' onclick=\"layer.closeAll()\">" +
			lan.public.close +
			"</button> <button type='button' class='btn btn-success btn-sm' onclick=\"setPassword(1)\">" +
			lan.public.edit +
			'</button></div></div>',
	});
}

function randPwd() {
	var pwd = RandomStrPwd(12);
	$('#p1').val(pwd);
	$('#p2').val(pwd);
	layer.msg(lan.bt.pass_rep_ps, { time: 2000 });
}

function setUserName(a) {
	if (a == 1) {
		p1 = $('#p1').val();
		p2 = $('#p2').val();
		if (p1 == '' || p1.length < 3) {
			layer.msg(lan.bt.user_len, {
				icon: 2,
			});
			return;
		}
		if (p1 != p2) {
			layer.msg(lan.bt.user_err_re, {
				icon: 2,
			});
			return;
		}
		var checks = ['admin', 'root', 'admin123', '123456'];

		if ($.inArray(p1, checks) >= 0) {
			layer.msg(lan.public.usually_username_ban, {
				icon: 2,
			});
			return;
		}

		var pdata = {
			username1: rsa.encrypt_public(p1),
			username2: rsa.encrypt_public(p2),
		};

		$.post('/config?action=setUsername', pdata, function (b) {
			if (b.status) {
				layer.closeAll();
				layer.msg(
					b.msg,
					{
						icon: 1,
						time: 1000,
					},
					function () {
						window.location.href = '/login?dologin=True';
					}
				);
				$("input[name='username_']").val(p1);
			} else {
				layer.msg(b.msg, {
					icon: 2,
				});
			}
		});
		return;
	}
	layer.open({
		type: 1,
		area: '290px',
		title: lan.bt.user_title,
		closeBtn: 2,
		shift: 5,
		shadeClose: false,
		content:
			"<div class='bt-form pd20 pb70'><div class='line'><span class='tname'>" +
			lan.bt.user +
			"</span><div class='info-r'><input class='bt-input-text' type='text' name='password1' id='p1' value='' placeholder='" +
			lan.bt.user_new +
			"' style='width:100%'/></div></div><div class='line'><span class='tname'>" +
			lan.bt.pass_re +
			"</span><div class='info-r'><input class='bt-input-text' type='text' name='password2' id='p2' value='' placeholder='" +
			lan.bt.pass_re_title +
			"' style='width:100%'/></div></div><div class='bt-form-submit-btn'><button type='button' class='btn btn-danger btn-sm' onclick=\"layer.closeAll()\">" +
			lan.public.close +
			"</button> <button type='button' class='btn btn-success btn-sm' onclick=\"setUserName(1)\">" +
			lan.public.edit +
			'</button></div></div>',
	});
}
var openWindow = null;
var downLoad = null;
var speed = null;

function task() {
	messagebox();
}

function ActionTask() {
	var a = layer.msg(lan.public.the_del, {
		icon: 16,
		time: 0,
		shade: [0.3, '#000'],
	});
	$.post('/files?action=ActionTask', '', function (b) {
		layer.close(a);
		layer.msg(b.msg, {
			icon: b.status ? 1 : 5,
		});
	});
}

function RemoveTask(id) {
	var loadT = bt.load(lan.public.the_del);
	bt.send('RemoveTask', 'files/RemoveTask', { id: id }, function (res) {
		bt.msg(res);
		reader_realtime_tasks();
	});
}

function GetTaskList(a) {
	a = a == undefined ? 1 : a;
	$.post('/data?action=getData', 'tojs=GetTaskList&table=tasks&limit=10&p=' + a, function (g) {
		var e = '';
		var b = '';
		var c = '';
		var f = false;
		for (var d = 0; d < g.data.length; d++) {
			switch (g.data[d].status) {
				case '-1':
					f = true;
					if (g.data[d].type != 'download') {
						b =
							"<li><span class='titlename'>" +
							g.data[d].name +
							"</span><span class='state'>" +
							lan.bt.task_install +
							" <img src='/static/img/ing.gif'> | <a href=\"javascript:RemoveTask(" +
							g.data[d].id +
							')">' +
							lan.public.close +
							"</a></span><span class='opencmd'></span><pre class='cmd'></pre></li>";
					} else {
						b =
							"<li><div class='line-progress' style='width:0%'></div><span class='titlename'>" +
							g.data[d].name +
							"<a id='speed' style='margin-left:130px;'>0.0M/12.5M</a></span><span class='com-progress'>0%</span><span class='state'>" +
							lan.bt.task_downloading +
							" <img src='/static/img/ing.gif'> | <a href=\"javascript:RemoveTask(" +
							g.data[d].id +
							')">' +
							lan.public.close +
							'</a></span></li>';
					}
					break;
				case '0':
					c +=
						"<li><span class='titlename'>" +
						g.data[d].name +
						"</span><span class='state'>" +
						lan.bt.task_sleep +
						'</span> | <a href="javascript:RemoveTask(' +
						g.data[d].id +
						')">' +
						lan.public.del +
						'</a></li>';
					break;
				case '1':
					e +=
						"<li><span class='titlename'>" +
						g.data[d].name +
						"</span><span class='state'>" +
						g.data[d].addtime +
						'  ' +
						lan.bt.task_ok +
						'  ' +
						lan.bt.time +
						(g.data[d].end - g.data[d].start) +
						lan.bt.s +
						'</span></li>';
			}
		}
		$('#srunning').html(b + c);
		$('#sbody').html(e);
		return f;
	});
}

function GetTaskCount() {
	$.post('/ajax?action=GetTaskCount', '', function (a) {
		if (a.status === false) {
			window.location.href = '/login?dologin=True';
			return;
		}
		$('.task').text(a);
	});
}

function setSelectChecked(c, d) {
	var a = document.getElementById(c);
	for (var b = 0; b < a.options.length; b++) {
		if (a.options[b].innerHTML == d) {
			a.options[b].selected = true;
			break;
		}
	}
}
GetTaskCount();

function RecInstall() {
	$.getScript('jquery.fly.min.js.js');
	$.post('/ajax?action=GetSoftList', '', function (l) {
		var c = '';
		var g = '';
		var e = '';
		for (var h = 0; h < l.length; h++) {
			if (l[h].name == 'Tomcat') {
				continue;
			}
			var o = '';
			var m = "<input id='data_" + l[h].name + "' data-info='" + l[h].name + ' ' + l[h].versions[0].version + "' type='checkbox' checked>";
			for (var b = 0; b < l[h].versions.length; b++) {
				var d = '';
				if (
					(l[h].name == 'PHP' && (l[h].versions[b].version == '5.4' || l[h].versions[b].version == '54')) ||
					(l[h].name == 'MySQL' && l[h].versions[b].version == '5.5') ||
					(l[h].name == 'phpMyAdmin' && l[h].versions[b].version == '4.4')
				) {
					d = 'selected';
					m = "<input id='data_" + l[h].name + "' data-info='" + l[h].name + ' ' + l[h].versions[b].version + "' type='checkbox' checked>";
				}
				o += "<option value='" + l[h].versions[b].version + "' " + d + '>' + l[h].name + ' ' + l[h].versions[b].version + '</option>';
			}
			var f =
				"<li><span class='ico'><img src='/static/img/" +
				l[h].name.toLowerCase() +
				".png'></span><span class='name'><select id='select_" +
				l[h].name +
				"' class='sl-s-info'>" +
				o +
				"</select></span><span class='pull-right'>" +
				m +
				'</span></li>';
			if (l[h].name == 'Nginx') {
				c = f;
			} else {
				if (l[h].name == 'Apache') {
					g = f;
				} else {
					e += f;
				}
			}
		}
		c += e;
		g += e;
		g = g.replace(new RegExp(/(data_)/g), 'apache_').replace(new RegExp(/(select_)/g), 'apache_select_');
		var k = layer.open({
			type: 1,
			title: lan.bt.install_title,
			area: ['666px', '473px'],
			closeBtn: 2,
			shadeClose: false,
			content:
				"<div class='rec-install'><div class='important-title'><p><span class='glyphicon glyphicon-alert' style='color: #f39c12; margin-right: 10px;'></span>" +
				lan.bt.install_ps +
				" <a href='javascript:jump()' style='color:#20a53a'>" +
				lan.bt.install_s +
				'</a> ' +
				lan.bt.install_s1 +
				"</p></div><div class='rec-box'><h3>" +
				lan.bt.install_lnmp +
				"</h3><div class='rec-box-con'><ul class='rec-list'>" +
				c +
				"</ul><p class='fangshi'>" +
				lan.bt.install_type +
				"：<label data-title='" +
				lan.bt.install_rpm_title +
				"' style='margin-right:0'>" +
				lan.bt.install_rpm +
				"<input type='checkbox' checked></label><label data-title='" +
				lan.bt.install_src_title +
				"'>" +
				lan.bt.install_src +
				"<input type='checkbox'></label></p><div class='onekey'>" +
				lan.bt.install_key +
				"</div></div></div><div class='rec-box' style='margin-left:16px'><h3>LAMP</h3><div class='rec-box-con'><ul class='rec-list'>" +
				g +
				"</ul><p class='fangshi'>" +
				lan.bt.install_type +
				"：<label data-title='" +
				lan.bt.install_rpm_title +
				"' style='margin-right:0'>" +
				lan.bt.install_rpm +
				"<input type='checkbox' checked></label><label data-title='" +
				lan.bt.install_src_title +
				"'>" +
				lan.bt.install_src +
				"<input type='checkbox'></label></p><div class='onekey'>" +
				lan.public.onclick_install +
				'</div></div></div></div>',
		});
		$('.fangshi input').click(function () {
			$(this).attr('checked', 'checked').parent().siblings().find('input').removeAttr('checked');
		});
		$('.sl-s-info').change(function () {
			var p = $(this).find('option:selected').text();
			var n = $(this).attr('id');
			p = p.toLowerCase();
			$(this).parents('li').find('input').attr('data-info', p);
		});
		$('#apache_select_PHP').change(function () {
			var n = $(this).val();
			j(n, 'apache_select_', 'apache_');
		});
		$('#select_PHP').change(function () {
			var n = $(this).val();
			j(n, 'select_', 'data_');
		});

		function j(p, r, q) {
			var n = '4.4';
			switch (p) {
				case '5.2':
					n = '4.0';
					break;
				case '5.3':
					n = '4.0';
					break;
				case '5.4':
					n = '4.4';
					break;
				case '5.5':
					n = '4.4';
					break;
				default:
					n = '4.7';
			}
			$('#' + r + "phpMyAdmin option[value='" + n + "']")
				.attr('selected', 'selected')
				.siblings()
				.removeAttr('selected');
			$('#' + r + '_phpMyAdmin').attr('data-info', 'phpmyadmin ' + n);
		}
		$('#select_MySQL,#apache_select_MySQL').change(function () {
			var n = $(this).val();
			a(n);
		});

		$('#apache_select_Apache').change(function () {
			var apacheVersion = $(this).val();
			if (apacheVersion == '2.2') {
				layer.msg(lan.bt.install_apache22);
			} else {
				layer.msg(lan.bt.install_apache24);
			}
		});

		$('#apache_select_PHP').change(function () {
			var apacheVersion = $('#apache_select_Apache').val();
			var phpVersion = $(this).val();
			if (apacheVersion == '2.2') {
				if (phpVersion != '5.2' && phpVersion != '5.3' && phpVersion != '5.4') {
					layer.msg(lan.bt.insatll_s22 + 'PHP-' + phpVersion, { icon: 5 });
					$(this).val('5.4');
					$('#apache_PHP').attr('data-info', 'php 5.4');
					return false;
				}
			} else {
				if (phpVersion == '5.2') {
					layer.msg(lan.bt.insatll_s24 + 'PHP-' + phpVersion, { icon: 5 });
					$(this).val('5.4');
					$('#apache_PHP').attr('data-info', 'php 5.4');
					return false;
				}
			}
		});

		function a(n) {
			memSize = getCookie('memSize');
			max = 64;
			msg = '64M';
			switch (n) {
				case '5.1':
					max = 256;
					msg = '256M';
					break;
				case '5.7':
					max = 1500;
					msg = '2GB';
					break;
				case '5.6':
					max = 800;
					msg = '1GB';
					break;
				case 'AliSQL':
					max = 800;
					msg = '1GB';
					break;
				case 'mariadb_10.0':
					max = 800;
					msg = '1GB';
					break;
				case 'mariadb_10.1':
					max = 1500;
					msg = '2GB';
					break;
			}
			if (memSize < max) {
				layer.msg(lan.bt.insatll_mem.replace('{1}', msg).replace('{2}', n), {
					icon: 5,
				});
			}
		}
		var de = null;
		$('.onekey').click(function () {
			if (de) return;
			var v = $(this).prev().find('input').eq(0).prop('checked') ? '1' : '0';
			var r = $(this).parents('.rec-box-con').find('.rec-list li').length;
			var n = '';
			var q = '';
			var p = '';
			var x = '';
			var s = '';
			de = true;
			for (var t = 0; t < r; t++) {
				var w = $(this).parents('.rec-box-con').find('ul li').eq(t);
				var u = w.find('input');
				if (u.prop('checked')) {
					n += u.attr('data-info') + ',';
				}
			}
			q = n.split(',');
			loadT = layer.msg(lan.bt.install_to, {
				icon: 16,
				time: 0,
				shade: [0.3, '#000'],
			});
			for (var t = 0; t < q.length - 1; t++) {
				p = q[t].split(' ')[0].toLowerCase();
				x = q[t].split(' ')[1];
				s = 'name=' + p + '&version=' + x + '&type=' + v + '&id=' + (t + 1);
				$.ajax({
					url: '/files?action=InstallSoft',
					data: s,
					type: 'POST',
					async: false,
					success: function (y) {},
				});
			}
			layer.close(loadT);
			layer.close(k);
			setTimeout(function () {
				GetTaskCount();
			}, 2000);
			layer.msg(lan.bt.install_ok, {
				icon: 1,
			});
			setTimeout(function () {
				task();
			}, 1000);
		});
		InstallTips();
		fly('onekey');
	});
}

// 校验
var checkout = {
	paw_verify_arry: ['admin888', '12345678', 'asdfghjkl', 'password'],
	// 验证邮箱
	check_email: function (el) {
		var code = $(el).val();
		var reg = /^[a-zA-Z0-9_.-]+@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*\.[a-zA-Z0-9]{2,6}$/;
		if (code.length != '') {
			if (!reg.test(code)) {
				layer.msg('Please input the correct email address.', { icon: 0 });
				return false;
			} else {
				return true;
			}
		} else {
			layer.msg('Please input the email address.', { icon: 0 });
			return false;
		}
	},
	// 密码效验
	paw_verify: function (el, verify) {
		var paw_val = $(el).val();
		if (paw_val.length == '') {
			layer.msg('Please enter password.', { icon: 0 });
			return false;
		} else if (paw_val.length < 8) {
			layer.msg('Password length is less than 8 digits.', { icon: 0 });
			return false;
		} else {
			// 检查弱口令
			var cps = paw_val.toLowerCase(); //全部转小写
			var isError = '';
			for (var i = 0; i < this.paw_verify_arry.length; i++) {
				if (cps == this.paw_verify_arry[i]) {
					isError += '[' + this.paw_verify_arry[i] + '] ';
				}
			}
			if (isError != '') {
				layer.msg('Please do not set a weak password:' + isError + ',Please re-enter your password.', { icon: 0 });
				return false;
			} else {
				return true;
			}
		}
	},
};

// 注册即送7天专业版授权和3年APP插件授权
function loginActivity() {
	layer.open({
		type: 1,
		title: '',
		area: '950px',
		closeBtn: 0,
		shadeClose: false,
		content:
			'<div style="display:flex">' +
			'<div style="width:450px;background: linear-gradient(0deg, #d8efdb, #edf7ef);padding:50px 30px;">' +
			'<p style="font-size:30px;margin-bottom:40px;font-weight: bold;">Log in to aaPanel account</p>' +
			'<p style="font-size:14px;margin-bottom:15px">SSL certificate synchronization (coming soon)</p>' +
			'<p style="font-size:14px;margin-bottom:15px">Receive service exception information (coming soon)</p>' +
			'<p style="font-size:14px;margin-bottom:15px;margin-left:5px;">·Website application firewall (WAF)</p>' +
			'<p style="font-size:14px;margin-bottom:15px;margin-left:5px;">·Website tamper-proof</p>' +
			'<p style="font-size:14px;margin-bottom:15px;margin-left:5px;">·File synchronization tool</p>' +
			'<p style="font-size:14px;margin-bottom:15px;margin-left:5px;">·Website analysis</p>' +
			'<p style="font-size:14px;margin-bottom:15px;">·aaPanel Mobile (APP)</p>' +
			'</div>' +
			'<div style="width:500px;padding:60px 30px; position: relative;">' +
			'<span id="signupPagBtn" style="font-size: 16px; cursor: pointer; border-bottom: 2px solid #20A53A; padding: 10px 0; color:#20A53A;">Sign up</span>' +
			'<span id="loginPagBtn" style="font-size: 16px; cursor: pointer;  padding: 10px 0; margin-left:30px;">Login</span>' +
			// '<div style="width:100%;height:2px;background-color:#F0F0F0; margin-top:15px;"></div>' +
			// 注册页面
			'<div id="signPag">' +
			'<div style="font-size:15px; margin: 36px 0 50px 0;">Register to get 3-year APP license</div>' +
			// 邮箱
			'<div style="display:flex;align-items: center; font-size:14px; margin-bottom:30px;"><span style="width:65px;text-align:right;margin-right:10px">Email</span><input id="singupUsername" name="username2" style="width:300px;border: 1px solid #ccc;padding-left: 5px; border-radius: 2px;height:35px" type="text" placeholder="Email" id="p1"></div>' +
			// 密码
			'<div style="display:flex;align-items: center;font-size:14px; margin-bottom:30px;"><span style="width:65px;text-align:right;margin-right:10px">Password</span><input id="singupPassword" autocomplete="new-password" style="width:300px;border: 1px solid #ccc;padding-left: 5px; border-radius: 2px;height:35px" type="password" name="password2"  placeholder="Password" id="p2"></div>' +
			'<div style="font-size:14px;"><input id="registerBtn" class="login-button" style="width:300px;margin-left:77px;color:#fff;height:40px;border-radius:2px; border:none" value="Register for free now" type="button"></div>' +
			'</div>' +
			// 验证邮件发送成功页面
			'<div id="mailboxPag" style="display:none">' +
			'<p style="font-size:25px; margin: 0 0 20px 0; font-weight: bold; word-break: break-all;">The verification email has been <br />sent to: <span class="email" style="text-decoration: underline; text-underline-offset: 7px;">aaaaaaaaaaaaaaaaaaaaaaaaaaaa@aaaaaaaaaaaaaa.com</span></p>' +
			'<p style="font-size:16px; margin: 20px 0 50px 0;">If you cannot receive the verification email, please use your registered email to contact: <span style="text-decoration: underline;">support@aapanel.com</span></p>' +
			'<div>' +
			'<button id="verified" style="width:200px; font-size:14px; background-color: #20a53a; border-color: transparent; height: 40px; cursor: pointer; color: #fff; border: none; border-radius: 2px;">I have verified</button>' +
			'<button id="resend" style="width:100px; font-size:14px; background-color: #ffffff; border: 1px solid #20a53a; height: 40px; cursor: pointer; color: #20a53a; border-radius: 2px; margin-left:20px;">Resend</button>' +
			'</div>' +
			'</div>' +
			'<div style=" display:flex; flex-direction: row-reverse; "><button id="skip" style="position: absolute;bottom: 10px; right: 10px;color:#BBBBBB;background-color:#fff;border:none;font-size:14px;">Skip</button></div>' +
			// 登陆页面
			'<div id="loginPag" style="display:none">' +
			'<div style="margin:50px 0"></div>' +
			// 邮箱
			'<div style="display:flex;align-items: center; font-size:14px; margin-bottom:30px;"><span style="width:65px;text-align:right;margin-right:10px">Email</span><input id="usernameInput" name="username2" style="width:300px;border: 1px solid #ccc;padding-left: 5px; border-radius: 2px;height:35px" type="text" placeholder="Email" id="p3"></div>' +
			// 密码
			'<div style="display:flex;align-items: center;font-size:14px; margin-bottom:30px;"><span style="width:65px;text-align:right;margin-right:10px">Password</span><input id="passwordInput" autocomplete="new-password" style="width:300px;border: 1px solid #ccc;padding-left: 5px; border-radius: 2px;height:35px" type="password" name="password2"  placeholder="Password" id="p4"></div>' +
			'<div style="font-size:14px;"><input class="login-button" id="loginBtn" style="width:300px;margin-left:77px;color:#fff;height:40px;border-radius:2px; border:none" value="Login" type="button"></div>' +
			'</div>' +
			'</div> ' +
			'</div>',
		success: function (layero, layerIndex) {
			var signupBtn = layero.find('#signupPagBtn');
			var loginBtn = layero.find('#loginPagBtn');
			var signupPage = layero.find('#signPag');
			var loginPage = layero.find('#loginPag');
			var mailboxPage = layero.find('#mailboxPag');
			var login = layero.find('#loginBtn');
			var verified = layero.find('#verified');
			var skip = layero.find('#skip');

			var showMailboxPage = false; // 是否显示验证邮箱页面

			signupBtn.on('click', function () {
				signupBtn.css({
					'font-size': '16px',
					cursor: 'pointer',
					'border-bottom': '2px solid #20A53A',
					padding: '10px 0',
					color: '#20A53A',
				});
				loginBtn.css({
					'font-size': '16px',
					cursor: 'pointer',
					padding: '10px 0',
					'margin-left': '30px',
					'border-bottom': 'none',
					color: 'black',
				});

				loginPage.hide();
				if (showMailboxPage === true) {
					mailboxPage.show();
					signupPage.hide();
				} else {
					mailboxPage.hide();
					signupPage.show();
				}
			});

			loginBtn.on('click', function () {
				signupBtn.css({
					'font-size': '16px',
					cursor: 'pointer',
					padding: '10px 0',
					'border-bottom': 'none',
					color: 'black',
				});
				loginBtn.css({
					'font-size': '16px',
					cursor: 'pointer',
					'border-bottom': '2px solid #20A53A',
					padding: '10px 0',
					color: '#20A53A',
					'margin-left': '30px',
				});

				signupPage.hide();
				mailboxPage.hide();
				loginPage.show();
			});

			// 登录
			login.on('click', function () {
				var username = layero.find('#usernameInput').val(); // 获取用户名输入框的值
				var password = layero.find('#passwordInput').val(); // 获取密码输入框的值
				// 检查用户名是否为空
				if (username === '') {
					layer.msg('Please enter a username.', { icon: 0 });
					return;
				}
				// 检查密码是否为空
				if (password === '') {
					layer.msg('Please enter a password.', { icon: 0 });
					return;
				}
				bt.pub.login_btname(username, password, function (ret) {
					if (ret.status) window.location.reload();
				});
			});

			var registerBtn = layero.find('#registerBtn');
			var resendBtn = layero.find('#resend');

			// 注册
			registerBtn.on('click', function () {
				localStorage.setItem('loginActivityShown', 'true');

				var username = layero.find('#singupUsername').val(); // 获取用户名输入框的值
				var password = layero.find('#singupPassword').val(); // 获取密码输入框的值

				if (!checkout.check_email('#singupUsername')) return;

				if (!checkout.paw_verify('#singupPassword')) return;

				var loadT = bt.load('Registering...');
				$.ajax({
					type: 'POST',
					url: '/userRegister?action=toRegister',
					data: { email: username, password: password },
					timeout: undefined,
					success: function (rdata) {
						loadT.close();
						if (rdata.status === true) {
							layer.msg(rdata.msg, { icon: 1 });
							$('#mailboxPag').find('.email').text(username);
							showMailboxPage = true;
							mailboxPage.show();
							loginPage.hide();
							signupPage.hide();
							signupBtn.hide();
							loginBtn.hide();
						} else {
							layer.msg(rdata.msg, { icon: 2 });
						}
					},
					error: function (ex) {
						layer.close(loadT);
						if (!callback) {
							layer.msg('Error found during request process!', { icon: 2 });
							return;
						}
						return callback(ex);
					},
				});
			});

			// 我已验证按钮
			verified.on('click', function () {
				window.location.reload();
				// soft.flush_cache();
				index.get_cloud_list();
			});

			// 重新发送邮箱验证
			resendBtn.on('click', function () {
				var username = layero.find('#singupUsername').val(); // 获取用户名输入框的值
				var password = layero.find('#singupPassword').val(); // 获取密码输入框的值

				var loadT = bt.load('Resending verification email...');
				$.ajax({
					type: 'POST',
					url: '/userRegister?action=toRegister',
					data: { email: username, password: password },
					timeout: undefined,
					success: function (rdata) {
						loadT.close();
						if (rdata.status === true) {
							layer.msg(rdata.msg, { icon: 1 });
							$('#mailboxPag').find('.email').text(email);
							showMailboxPage = true;
							mailboxPage.show();
							// loginPage.hide();
							signupPage.hide();
						} else {
							layer.msg(rdata.msg, { icon: 2 });
						}
					},
					error: function (ex) {
						layer.close(loadT);
						if (!callback) {
							layer.msg('Error found during request process!', { icon: 2 });
							return;
						}
						return callback(ex);
					},
				});
			});

			// 跳过按钮
			skip.on('click', function () {
				localStorage.setItem('loginActivityShown', 'true');
				if (showMailboxPage === true) {
					layer.close(layerIndex);
					window.location.reload();
					index.get_cloud_list();
				} else {
					layer.close(layerIndex);
					index.get_cloud_list();
				}
			});
		},
	});
}
function jump() {
	layer.closeAll();
	window.location.href = '/soft';
}

function InstallTips() {
	$('.fangshi label')
		.mouseover(function () {
			var a = $(this).attr('data-title');
			layer.tips(a, this, {
				tips: [1, '#787878'],
				time: 0,
			});
		})
		.mouseout(function () {
			$('.layui-layer-tips').remove();
		});
}

function fly(a) {
	var b = $('#task').offset();
	$('.' + a).click(function (d) {
		var e = $(this);
		var c = $('<span class="yuandian"></span>');
		c.fly({
			start: {
				left: d.pageX,
				top: d.pageY,
			},
			end: {
				left: b.left + 10,
				top: b.top + 10,
				width: 0,
				height: 0,
			},
			onEnd: function () {
				layer.closeAll();
				layer.msg(lan.bt.task_add, {
					icon: 1,
				});
				GetTaskCount();
			},
		});
	});
}

//检查选中项
function checkSelect() {
	setTimeout(function () {
		var checkList = $('input[name=id]');
		var count = 0;
		for (var i = 0; i < checkList.length; i++) {
			if (checkList[i].checked) count++;
		}
		if (count > 0) {
			$('#allDelete,#allExecute,#allLog').show();
		} else {
			$('#allDelete,#allExecute,#allLog').hide();
		}
	}, 5);
}

//处理排序
function listOrder(skey, type, obj) {
	or = getCookie('order');
	orderType = 'desc';
	if (or) {
		if (or.split(' ')[1] == 'desc') {
			orderType = 'asc';
		}
	}

	setCookie('order', skey + ' ' + orderType);

	switch (type) {
		case 'site':
			getWeb(1);
			break;
		case 'database':
			getData(1);
			break;
		case 'ftp':
			getFtp(1);
			break;
	}
	$(obj).find('.glyphicon-triangle-bottom').remove();
	$(obj).find('.glyphicon-triangle-top').remove();
	if (orderType == 'asc') {
		$(obj).append("<span class='glyphicon glyphicon-triangle-bottom' style='margin-left:5px;color:#bbb'></span>");
	} else {
		$(obj).append("<span class='glyphicon glyphicon-triangle-top' style='margin-left:5px;color:#bbb'></span>");
	}
}

//去关联列表
function GetBtpanelList() {
	var con = '';
	$.post('/config?action=GetPanelList', function (rdata) {
		for (var i = 0; i < rdata.length; i++) {
			con +=
				'<h3 class="mypcip mypcipnew" style="opacity:.6" data-url="' +
				rdata[i].url +
				'" data-user="' +
				rdata[i].username +
				'" data-pw="' +
				rdata[i].password +
				'"><span class="f14 cw">' +
				rdata[i].title +
				'</span><em class="btedit" onclick="bindBTPanel(0,\'c\',\'' +
				rdata[i].title +
				"','" +
				rdata[i].id +
				"','" +
				rdata[i].url +
				"','" +
				rdata[i].username +
				"','" +
				rdata[i].password +
				'\')"></em></h3>';
		}
		$('#newbtpc').html(con);
		$('.mypcipnew')
			.hover(
				function () {
					$(this).css('opacity', '1');
				},
				function () {
					$(this).css('opacity', '.6');
				}
			)
			.click(function () {
				$('#btpanelform').remove();
				var murl = $(this).attr('data-url');
				var user = $(this).attr('data-user');
				var pw = $(this).attr('data-pw');
				layer.open({
					type: 2,
					title: false,
					closeBtn: 0, //不显示关闭按钮
					shade: [0],
					area: ['340px', '215px'],
					offset: 'rb', //右下角弹出
					time: 5, //2秒后自动关闭
					anim: 2,
					content: [murl + '/login', 'no'],
				});
				var loginForm =
					'<div id="btpanelform" style="display:none"><form id="toBtpanel" action="' +
					murl +
					'/login" method="post" target="btpfrom">\
				<input name="username" id="btp_username" value="' +
					user +
					'" type="text">\
				<input name="password" id="btp_password" value="' +
					pw +
					'" type="password">\
				<input name="code" id="bt_code" value="12345" type="text">\
			</form><iframe name="btpfrom" src=""></iframe></div>';
				$('body').append(loginForm);
				layer.msg(lan.bt.panel_open, { icon: 16, shade: [0.3, '#000'], time: 1000 });
				setTimeout(function () {
					$('#toBtpanel').submit();
				}, 500);
				setTimeout(function () {
					window.open(murl);
				}, 1000);
			});
		$('.btedit').click(function (e) {
			e.stopPropagation();
		});
	});
}
GetBtpanelList();
//添加面板快捷登录
function bindBTPanel(a, type, ip, btid, url, user, pw) {
	var titleName = lan.bt.panel_add;
	if (type == 'b') {
		btn = "<button type='button' class='btn btn-success btn-sm' onclick=\"bindBTPanel(1,'b')\">" + lan.public.add + '</button>';
	} else {
		titleName = lan.bt.panel_edit + ip;
		btn =
			"<button type='button' class='btn btn-default btn-sm' onclick=\"bindBTPaneldel('" +
			btid +
			'\')">' +
			lan.public.del +
			"</button><button type='button' class='btn btn-success btn-sm' onclick=\"bindBTPanel(1,'c','" +
			ip +
			"','" +
			btid +
			"')\" style='margin-left:7px'>" +
			lan.public.edit +
			'</button>';
	}
	if (url == undefined) url = 'http://';
	if (user == undefined) user = '';
	if (pw == undefined) pw = '';
	if (ip == undefined) ip = '';
	if (a == 1) {
		var gurl = '/config?action=AddPanelInfo';
		var btaddress = $('#btaddress').val();
		if (!btaddress.match(/^(http|https)+:\/\/([\w-]+\.)+[\w-]+:\d+/)) {
			layer.msg(lan.bt.panel_err_format + '<p>http://192.168.0.1:8888</p>', { icon: 5, time: 5000 });
			return;
		}
		var btuser = encodeURIComponent($('#btuser').val());
		var btpassword = encodeURIComponent($('#btpassword').val());
		var bttitle = $('#bttitle').val();
		var data = 'title=' + bttitle + '&url=' + encodeURIComponent(btaddress) + '&username=' + btuser + '&password=' + btpassword;
		if (btaddress == '' || btuser == '' || btpassword == '' || bttitle == '') {
			layer.msg(lan.bt.panel_err_empty, { icon: 8 });
			return;
		}
		if (type == 'c') {
			gurl = '/config?action=SetPanelInfo';
			data = data + '&id=' + btid;
		}
		$.post(gurl, data, function (b) {
			if (b.status) {
				layer.closeAll();
				layer.msg(b.msg, { icon: 1 });
				GetBtpanelList();
			} else {
				layer.msg(b.msg, { icon: 2 });
			}
		});
		return;
	}
	layer.open({
		type: 1,
		area: '400px',
		title: titleName,
		closeBtn: 2,
		shift: 5,
		shadeClose: false,
		content:
			"<div class='bt-form pd20 pb70'>\
		<div class='line'><span class='tname'>" +
			lan.bt.panel_address +
			"</span>\
		<div class='info-r'><input class='bt-input-text' type='text' name='btaddress' id='btaddress' value='" +
			url +
			"' placeholder='" +
			lan.bt.panel_address +
			"' style='width:100%'/></div>\
		</div>\
		<div class='line'><span class='tname'>" +
			lan.bt.panel_user +
			"</span>\
		<div class='info-r'><input class='bt-input-text' type='text' name='btuser' id='btuser' value='" +
			user +
			"' placeholder='" +
			lan.bt.panel_user +
			"' style='width:100%'/></div>\
		</div>\
		<div class='line'><span class='tname'>" +
			lan.bt.panel_pass +
			"</span>\
		<div class='info-r'><input class='bt-input-text' type='password' name='btpassword' id='btpassword' value='" +
			pw +
			"' placeholder='" +
			lan.bt.panel_pass +
			"' style='width:100%'/></div>\
		</div>\
		<div class='line'><span class='tname'>" +
			lan.bt.panel_ps +
			"</span>\
		<div class='info-r'><input class='bt-input-text' type='text' name='bttitle' id='bttitle' value='" +
			ip +
			"' placeholder='" +
			lan.bt.panel_ps +
			"' style='width:100%'/></div>\
		</div>\
		<div class='line'><ul class='help-info-text c7'><li>" +
			lan.bt.panel_ps_1 +
			'</li><li>' +
			lan.bt.panel_ps_2 +
			'</li><li>' +
			lan.bt.panel_ps_3 +
			"</li></ul></div>\
		<div class='bt-form-submit-btn'><button type='button' class='btn btn-danger btn-sm' onclick=\"layer.closeAll()\">" +
			lan.public.close +
			'</button> ' +
			btn +
			'</div></div>',
	});
	$('#btaddress')
		.on('input', function () {
			var str = $(this).val();
			var isip = /([\w-]+\.){2,6}\w+/;
			var iptext = str.match(isip);
			if (iptext) $('#bttitle').val(iptext[0]);
		})
		.blur(function () {
			var str = $(this).val();
			var isip = /([\w-]+\.){2,6}\w+/;
			var iptext = str.match(isip);
			if (iptext) $('#bttitle').val(iptext[0]);
		});
}
//删除快捷登录
function bindBTPaneldel(id) {
	$.post('/config?action=DelPanelInfo', 'id=' + id, function (rdata) {
		layer.closeAll();
		layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
		GetBtpanelList();
	});
}

function getSpeed(sele) {
	if (!$(sele)) return;
	$.get('/ajax?action=GetSpeed', function (speed) {
		if (speed.title === null) return;
		mspeed = '';
		if (speed.speed > 0) {
			mspeed = '<span class="pull-right">' + ToSize(speed.speed) + '/s</span>';
		}
		body =
			'<p>' +
			speed.title +
			' <img src="/static/img/ing.gif"></p>\
		<div class="bt-progress"><div class="bt-progress-bar" style="width:' +
			speed.progress +
			'%"><span class="bt-progress-text">' +
			speed.progress +
			'%</span></div></div>\
		<p class="f12 c9"><span class="pull-left">' +
			speed.used +
			'/' +
			speed.total +
			'</span>' +
			mspeed +
			'</p>';
		$(sele).prev().hide();
		$(sele).css({ 'margin-left': '-37px', width: '380px' });
		$(sele).parents('.layui-layer').css({ 'margin-left': '-100px' });

		$(sele).html(body);
		setTimeout(function () {
			getSpeed(sele);
		}, 1000);
	});
}
//消息盒子
function messagebox() {
	layer.open({
		type: 1,
		title: lan.bt.task_title,
		area: '680px',
		closeBtn: 2,
		shadeClose: false,
		content:
			'<div class="bt-form">' +
			'<div class="bt-w-main">' +
			'<div class="bt-w-menu">' +
			'<p class="bgw">' +
			lan.bt.task_list +
			' (<span id="taskNum">0</span>)</p>' +
			'<p>' +
			lan.bt.task_msg +
			' (<span id="taskCompleteNum">0</span>)</p>' +
			'<p>' +
			lan.public.exec_log +
			'</p>' +
			'</div>' +
			'<div class="bt-w-con pd15">' +
			'<div class="bt-w-item active" id="command_install_list">\
						<ul class="cmdlist"></ul>\
						<div style="position: fixed;bottom: 15px;">' +
			lan.public.task_long_time_not_exec +
			'</div>\
					</div>' +
			'<div class="bt-w-item" id="messageContent"></div>' +
			'<div class="bt-w-item"><pre id="execLog" class="command_output_pre" style="height: 530px;"></pre></div>' +
			'</div>' +
			'</div>' +
			'</div>',
		success: function (layers, indexs) {
			$(layers)
				.find('.bt-w-menu p')
				.on('click', function () {
					var index = $(this).index();
					$(this).addClass('bgw').siblings().removeClass('bgw');
					$(layers)
						.find('.bt-w-con .bt-w-item:eq(' + index + ')')
						.addClass('active')
						.siblings()
						.removeClass('active');
					switch (index) {
						case 0:
							reader_realtime_tasks();
							break;
						case 1:
							reader_message_list();
							break;
						case 2:
							var loadT = bt.load('Getting execution log, please wait...');
							bt.send('GetExecLog', 'files/GetExecLog', {}, function (res) {
								loadT.close();
								var exec_log = $('#execLog');
								// console.log(exec_log)
								exec_log.html(res);
								exec_log[0].scrollTop = exec_log[0].scrollHeight;
							});
							break;
					}
				});
			reader_realtime_tasks();
			setTimeout(function () {
				reader_realtime_tasks();
			}, 1000);
			reader_message_list();
		},
	});
}

function get_message_data(page, callback) {
	if (typeof page === 'function') (callback = page), (page = 1);
	var loadT = bt.load('Getting message list, please wait...');
	bt.send(
		'getData',
		'data/getData',
		{
			tojs: 'reader_message_list',
			table: 'tasks',
			result: '2,4,6,8',
			limit: '11',
			search: '1',
			p: page,
		},
		function (res) {
			loadT.close();
			if (callback) callback(res);
		}
	);
}

function reader_message_list(page) {
	get_message_data(page, function (res) {
		var html = '',
			f = false,
			task_count = 0;
		for (var i = 0; i < res.data.length; i++) {
			var item = res.data[i];
			if (item.status !== '1') {
				task_count++;
				continue;
			}
			html +=
				'<tr><td><div class="titlename c3">' +
				item.name +
				'</span><span class="rs-status"> [' +
				lan.bt.task_ok +
				'] <span><span class="rs-time">' +
				lan.bt.time +
				' ' +
				(item.end - item.start) +
				' ' +
				lan.bt.s +
				'</span></div></td><td class="text-right c3">' +
				item.addtime +
				'</td></tr>';
		}
		var con =
			'<div class="divtable"><table class="table table-hover">\
					<thead><tr><th>' +
			lan.bt.task_name +
			'</th><th class="text-right">' +
			lan.bt.task_time +
			'</th></tr></thead>\
						<tbody id="remind">' +
			html +
			'</tbody>\
					</table></div>\
					<div class="mtb15" style="height:32px">\
						<div class="pull-left buttongroup" style="display:none;"><button class="btn btn-default btn-sm mr5 rs-del" disabled="disabled">' +
			lan.public.del +
			'</button><button class="btn btn-default btn-sm mr5 rs-read" disabled="disabled">' +
			lan.bt.task_tip_read +
			'</button><button class="btn btn-default btn-sm">' +
			lan.bt.task_tip_all +
			'</button></div>\
						<div id="taskPage" class="page"></div>\
					</div>';

		var msg_count = res.page.match(/\'Pcount\'>.+<\/span>/)[0].replace(/[^0-9]/gi, '');
		$('#taskCompleteNum').text(parseInt(msg_count) - task_count);
		$('#messageContent').html(con);
		$('#taskPage').html(res.page);
	});
}

function get_realtime_tasks(callback) {
	bt.send('GetTaskSpeed', 'files/GetTaskSpeed', {}, function (res) {
		if (callback) callback(res);
	});
}

var initTime = null,
	messageBoxWssock = null;

function reader_realtime_tasks(refresh) {
	get_realtime_tasks(function (res) {
		var command_install_list = $('#command_install_list'),
			loading =
				'data:image/gif;base64,R0lGODlhDgACAIAAAHNzcwAAACH/C05FVFNDQVBFMi4wAwEAAAAh+QQFDgABACwAAAAAAgACAAACAoRRACH5BAUOAAEALAQAAAACAAIAAAIChFEAIfkEBQ4AAQAsCAAAAAIAAgAAAgKEUQAh+QQJDgABACwAAAAADgACAAACBoyPBpu9BQA7',
			html = '',
			message = res.msg,
			task = res.task;
		$('#taskNum').html(typeof res.task === 'undefined' ? 0 : res.task.length);
		if (typeof res.task === 'undefined') {
			html = '<div style="padding:5px;">' + lan.bt.task_not_list + '</div><div style="position: fixed;bottom: 15px;">' + lan.public.task_long_time_not_exec + '</div>';

			command_install_list.html(html);
		} else {
			var shell = '',
				message_split = message.split('\n');
			var del_task = '<a style="color:green" onclick="RemoveTask($id)" href="javascript:;">' + lan.public.del + '</a>',
				loading_img = "<img src='" + loading + "'/>";
			for (var j = 0; j < message_split.length; j++) {
				shell += message_split[j] + '</br>';
			}
			// if(command_install_list.find('li').length){
			// 	if(command_install_list.find('li').length > res.task.length) command_install_list.find('li:eq(0)').remove();
			// 	if(task[0].status !== '0' && !command_install_list.find('pre').length) command_install_list.find('li:eq(0)').append('<pre class=\'cmd command_output_pre\'>' + shell +'</pre>')
			// 	messageBoxWssock.el = command_install_list.find('pre');
			// }else{
			for (var i = 0; i < task.length; i++) {
				var item = task[i],
					task_html = '';
				if (item.status === '-1' && item.type === 'download') {
					task_html =
						"<div class='line-progress' style='width:" +
						message.pre +
						"%'></div><span class='titlename'>" +
						item.name +
						"<a style='margin-left:130px;'>" +
						(ToSize(message.used) + '/' + ToSize(message.total)) +
						"</a></span><span class='com-progress'>" +
						message.pre +
						"%</span><span class='state'>" +
						lan.bt.task_downloading +
						' ' +
						loading_img +
						' | ' +
						del_task.replace('$id', item.id) +
						'</span>';
				} else {
					task_html += '<span class="titlename">' + item.name + '</span>';
					task_html += '<span class="state">';
					switch (item.status) {
						case '0':
							task_html += lan.bt.task_sleep + ' | ' + del_task.replace('$id', item.id);
							break;
						case '-1':
							var is_scan = item.name.indexOf('扫描') !== -1;
							task_html += (is_scan ? lan.bt.task_scan : lan.bt.task_install) + ' ' + loading_img + ' | ' + del_task.replace('$id', item.id);
							break;
					}
					task_html += '</span>';
					if (item.type !== 'download' && item.status === '-1') {
						task_html += "<pre class='cmd command_output_pre'>" + shell + '</pre>';
					}
				}
				html += '<li>' + task_html + '</li>';
			}
			command_install_list.find('ul').html(html);
			// }
			if (task.length > 0 && task[0].status === '0') {
				setTimeout(function () {
					reader_realtime_tasks(true);
				}, 100);
			}
			if (command_install_list.find('pre').length) {
				var pre = command_install_list.find('pre');
				pre.scrollTop(pre[0].scrollHeight);
			}
			if (!refresh) {
				messageBoxWssock = bt_tools.command_line_output({
					el: '#command_install_list .command_output_pre',
					area: ['100%', '200px'],
					shell: 'tail -n 100 -f /tmp/panelExec.log',
					message: function (res) {
						if (res.indexOf('|-Successify ---Script execution completed---') > -1) {
							setTimeout(function () {
								reader_realtime_tasks(true);
								reader_message_list();
							}, 100);
						}
					},
				});
			}
		}
	});
}

//取执行日志
function execLog() {
	$.post('/files?action=GetExecLog', {}, function (logs) {
		var lbody = '<textarea readonly="" style="margin: 0px;width: 551px;height: 520px;background-color: #333;color:#fff; padding:0 5px" id="exec_log">' + logs + '</textarea>';
		$('.taskcon').html(lbody);
		var ob = document.getElementById('exec_log');
		ob.scrollTop = ob.scrollHeight;
	});
}

function get_msg_data(a, fun) {
	a = a == undefined ? 1 : a;
	$.post('/data?action=getData', 'tojs=remind&table=tasks&result=2,4,6,8&limit=10&search=1&p=' + a, function (g) {
		fun(g);
	});
}

function remind(a) {
	get_msg_data(a, function (g) {
		var e = '';
		var f = false;
		var task_count = 0;
		for (var d = 0; d < g.data.length; d++) {
			if (g.data[d].status != '1') {
				task_count++;
				continue;
			}
			e +=
				'<tr><td><input type="checkbox"></td><td><div class="titlename c3" title="' +
				g.data[d].name +
				g.data[d].addtime +
				lan.bt.task_ok +
				lan.bt.time +
				(g.data[d].end - g.data[d].start) +
				lan.bt.s +
				'">' +
				g.data[d].name +
				g.data[d].addtime +
				'</span><span class="rs-status">【' +
				lan.bt.task_ok +
				'】<span><span class="rs-time">' +
				lan.bt.time +
				(g.data[d].end - g.data[d].start) +
				lan.bt.s +
				'</span></div></td><td class="text-right c3">' +
				g.data[d].addtime +
				'</td></tr>';
		}
		var con =
			'<div class="divtable"><table class="table table-hover">\
					<thead><tr><th width="20"><input id="Rs-checkAll" type="checkbox" onclick="RscheckSelect()"></th><th>' +
			lan.bt.task_name +
			'</th><th class="text-right">' +
			lan.bt.task_time +
			'</th></tr></thead>\
					<tbody id="remind">' +
			e +
			'</tbody>\
					</table></div>\
					<div class="mtb15" style="height:32px">\
						<div class="pull-left buttongroup" style="display:none;"><button class="btn btn-default btn-sm mr5 rs-del" disabled="disabled">' +
			lan.public.del +
			'</button><button class="btn btn-default btn-sm mr5 rs-read" disabled="disabled">' +
			lan.bt.task_tip_read +
			'</button><button class="btn btn-default btn-sm">' +
			lan.bt.task_tip_all +
			'</button></div>\
						<div id="taskPage" class="page"></div>\
					</div>';

		var msg_count = g.page.match(/\'Pcount\'>.+<\/span>/)[0].replace(/[^0-9]/gi, '');
		$('.msg_count').text(parseInt(msg_count) - task_count);
		$('.taskcon').html(con);
		$('#taskPage').html(g.page);
		$('#Rs-checkAll').click(function () {
			if ($(this).prop('checked')) {
				$('#remind').find('input').prop('checked', true);
			} else {
				$('#remind').find('input').prop('checked', false);
			}
		});
	});
}

function GetReloads() {
	var a = 0;
	var mm = $('#taskList').html();
	if (mm == undefined || mm.indexOf(lan.bt.task_list) == -1) {
		clearInterval(speed);
		a = 0;
		speed = null;
		return;
	}
	if (speed) return;
	speed = setInterval(function () {
		var mm = $('#taskList').html();
		if (mm == undefined || mm.indexOf(lan.bt.task_list) == -1) {
			clearInterval(speed);
			speed = null;
			a = 0;
			return;
		}
		a++;
		$.post('/files?action=GetTaskSpeed', '', function (h) {
			if (h.task == undefined) {
				$('.cmdlist').html(lan.bt.task_not_list);
				return;
			}

			if (h.status === false) {
				clearInterval(speed);
				speed = null;
				a = 0;
				return;
			}

			var b = '';
			var d = '';
			$('#task').text(h.task.length);
			$('.task_count').text(h.task.length);
			for (var g = 0; g < h.task.length; g++) {
				if (h.task[g].status == '-1') {
					if (h.task[g].type != 'download') {
						var c = '';
						var f = h.msg.split('\n');
						for (var e = 0; e < f.length; e++) {
							c += f[e] + '<br>';
						}
						if (h.task[g].name.indexOf(lan.public.scan) != -1) {
							b =
								"<li><span class='titlename'>" +
								h.task[g].name +
								"</span><span class='state'>" +
								lan.bt.task_scan +
								" <img src='/static/img/ing.gif'> | <a href=\"javascript:RemoveTask(" +
								h.task[g].id +
								')">' +
								lan.public.close +
								"</a></span><span class='opencmd'></span><div class='cmd'>" +
								c +
								'</div></li>';
						} else {
							b =
								"<li><span class='titlename'>" +
								h.task[g].name +
								"</span><span class='state'>" +
								lan.bt.task_install +
								" <img src='/static/img/ing.gif'> | <a href=\"javascript:RemoveTask(" +
								h.task[g].id +
								')">' +
								lan.public.close +
								"</a></span><div class='cmd'>" +
								c +
								'</div></li>';
						}
					} else {
						b =
							"<li><div class='line-progress' style='width:" +
							h.msg.pre +
							"%'></div><span class='titlename'>" +
							h.task[g].name +
							"<a style='margin-left:130px;'>" +
							(ToSize(h.msg.used) + '/' + ToSize(h.msg.total)) +
							"</a></span><span class='com-progress'>" +
							h.msg.pre +
							"%</span><span class='state'>" +
							lan.bt.task_downloading +
							" <img src='/static/img/ing.gif'> | <a href=\"javascript:RemoveTask(" +
							h.task[g].id +
							')">' +
							lan.public.close +
							'</a></span></li>';
					}
				} else {
					d +=
						"<li><span class='titlename'>" +
						h.task[g].name +
						"</span><span class='state'>" +
						lan.bt.task_sleep +
						" | <a style='color:green' href=\"javascript:RemoveTask(" +
						h.task[g].id +
						')">' +
						lan.public.del +
						'</a></span></li>';
				}
			}
			$('.cmdlist').html(b + d);
			$('.cmd').html(c);
			try {
				if ($('.cmd')[0].scrollHeight) $('.cmd').scrollTop($('.cmd')[0].scrollHeight);
			} catch (e) {
				return;
			}
		}).error(function () {});
	}, 1000);
}

//检查选中项
function RscheckSelect() {
	setTimeout(function () {
		var checkList = $('#remind').find('input');
		var count = 0;
		for (var i = 0; i < checkList.length; i++) {
			if (checkList[i].checked) count++;
		}
		if (count > 0) {
			$('.buttongroup .btn').removeAttr('disabled');
		} else {
			$('.rs-del,.rs-read').attr('disabled', 'disabled');
		}
	}, 5);
}

function tasklist(a) {
	var con = '<ul class="cmdlist"></ul><span style="position:  fixed;bottom: 13px;">' + lan.public.task_long_time_not_exec + '</span>';
	$('.taskcon').html(con);
	a = a == undefined ? 1 : a;
	$.post('/data?action=getData', 'tojs=GetTaskList&table=tasks&limit=10&p=' + a, function (g) {
		var e = '';
		var b = '';
		var c = '';
		var f = false;
		var task_count = 0;
		for (var d = 0; d < g.data.length; d++) {
			switch (g.data[d].status) {
				case '-1':
					f = true;
					if (g.data[d].type != 'download') {
						b =
							"<li><span class='titlename'>" +
							g.data[d].name +
							"</span><span class='state pull-right c6'>" +
							lan.bt.task_install +
							" <img src='/static/img/ing.gif'> | <a class='btlink' href=\"javascript:RemoveTask(" +
							g.data[d].id +
							')">' +
							lan.public.close +
							"</a></span><span class='opencmd'></span><pre class='cmd'></pre></li>";
					} else {
						b =
							"<li><div class='line-progress' style='width:0%'></div><span class='titlename'>" +
							g.data[d].name +
							"<a id='speed' style='margin-left:130px;'>0.0M/12.5M</a></span><span class='com-progress'>0%</span><span class='state'>" +
							lan.bt.task_downloading +
							" <img src='/static/img/ing.gif'> | <a href=\"javascript:RemoveTask(" +
							g.data[d].id +
							')">' +
							lan.public.close +
							'</a></span></li>';
					}
					task_count++;
					break;
				case '0':
					c +=
						"<li><span class='titlename'>" +
						g.data[d].name +
						"</span><span class='state pull-right c6'>" +
						lan.bt.task_sleep +
						'</span> | <a href="javascript:RemoveTask(' +
						g.data[d].id +
						")\" class='btlink'>" +
						lan.public.del +
						'</a></li>';
					task_count++;
					break;
			}
		}

		$('.task_count').text(task_count);

		get_msg_data(1, function (d) {
			var msg_count = d.page.match(/\'Pcount\'>.+<\/span>/)[0].replace(/[^0-9]/gi, '');
			$('.msg_count').text(parseInt(msg_count));
		});

		$('.cmdlist').html(b + c);
		GetReloads();
		return f;
	});
}

//检查登陆状态
function check_login() {
	$.post('/ajax?action=CheckLogin', {}, function (rdata) {
		if (rdata === true) return;
	});
}

//登陆跳转
function to_login() {
	layer.confirm(lan.public.login_expire, { title: lan.public.session_expire, icon: 2, closeBtn: 1, shift: 5 }, function () {
		location.reload();
	});
}
//表格头固定
function table_fixed(name) {
	var tableName = document.querySelector('#' + name);
	tableName.addEventListener('scroll', scroll_handle);
}

function scroll_handle(e) {
	var scrollTop = this.scrollTop;
	$(this)
		.find('thead')
		.css({ transform: 'translateY(' + scrollTop + 'px)', position: 'relative', 'z-index': '1' });
}
var clipboard, interval, socket, term, ssh_login, term_box;

var pdata_socket = {
	x_http_token: document.getElementById('request_token_head').getAttribute('token'),
};

var Term = {
	bws: null, //websocket对象
	route: '/webssh', //被访问的方法
	term: null,
	term_box: null,
	ssh_info: {},
	last_body: false,
	last_cd: null,
	config: {
		cols: 0,
		rows: 0,
		fontSize: 12,
	},

	// 	缩放尺寸
	detectZoom: (function () {
		var ratio = 0,
			screen = window.screen,
			ua = navigator.userAgent.toLowerCase();
		if (window.devicePixelRatio !== undefined) {
			ratio = window.devicePixelRatio;
		} else if (~ua.indexOf('msie')) {
			if (screen.deviceXDPI && screen.logicalXDPI) {
				ratio = screen.deviceXDPI / screen.logicalXDPI;
			}
		} else if (window.outerWidth !== undefined && window.innerWidth !== undefined) {
			ratio = window.outerWidth / window.innerWidth;
		}

		if (ratio) {
			ratio = Math.round(ratio * 100);
		}
		return ratio;
	})(),
	//连接websocket
	connect: function () {
		if (!Term.bws || Term.bws.readyState == 3 || Term.bws.readyState == 2) {
			//连接
			ws_url = (window.location.protocol === 'http:' ? 'ws://' : 'wss://') + window.location.host + Term.route;

			Term.bws = new WebSocket(ws_url);

			//绑定事件
			Term.bws.addEventListener('message', Term.on_message);
			Term.bws.addEventListener('close', Term.on_close);
			Term.bws.addEventListener('error', Term.on_error);
			Term.bws.addEventListener('open', Term.on_open);

			//if (Term.ssh_info) Term.send(JSON.stringify(Term.ssh_info))
		}
	},
	//连接服务器成功
	on_open: function (ws_event) {
		var http_token = $('#request_token_head').attr('token');
		Term.send(JSON.stringify({ 'x-http-token': http_token }));
		if (JSON.stringify(Term.ssh_info) !== '{}') Term.send(JSON.stringify(Term.ssh_info));
		// 		Term.term.FitAddon.fit();
		// 		Term.resize();
		// 		var f_path = $("#fileInputPath").val();
		var f_path = $('#fileInputPath').attr('data-path');
		if (f_path) {
			Term.last_cd = 'cd ' + f_path;
			Term.send(Term.last_cd + '\n');
		}
	},

	//服务器消息事件
	// on_message: function(ws_event) {
	//     result = ws_event.data;
	//     if (result === "\r'Server connection failed'!\r" || result === "\rWrong user name or password!\r") {
	//         show_ssh_login(result);
	//         Term.close();
	//         return;
	//     }
	//     Term.term.write(result);

	//     if (result == '\r\n登出\r\n' || result == '登出\r\n' || result == '\r\nlogout\r\n' || result == 'logout\r\n') {
	//         setTimeout(function() {
	//             layer.close(Term.term_box);
	//         }, 500);
	//         Term.close();
	//         Term.bws = null;
	//     }
	// },
	on_message: function (ws_event) {
		result = ws_event.data;
		if ((result.indexOf('@127.0.0.1:') != -1 || result.indexOf('@localhost:') != -1) && result.indexOf('Authentication failed') != -1) {
			Term.term.write(result);
			Term.localhost_login_form(result);
			Term.close();
			return;
		}
		if (Term.last_cd) {
			if (result.indexOf(Term.last_cd) != -1 && result.length - Term.last_cd.length < 3) {
				Term.last_cd = null;
				return;
			}
		}
		if (result === '\rServer connection failed!\r' || result == '\rWrong user name or password!\r') {
			Term.close();
			return;
		}
		if (result.length > 1 && Term.last_body === false) {
			Term.last_body = true;
		}
		Term.term.write(result);
		if (result == '\r\n登出\r\n' || result == '\r\n注销\r\n' || result == '注销\r\n' || result == '登出\r\n' || result == '\r\nlogout\r\n' || result == 'logout\r\n') {
			setTimeout(function () {
				layer.close(Term.term_box);
				Term.term.dispose();
			}, 500);
			Term.close();
			Term.bws = null;
		}
	},
	//websocket关闭事件
	on_close: function (ws_event) {
		Term.bws = null;
	},

	//websocket错误事件
	// on_error: function(ws_event) {
	//     if(ws_event.target.readyState === 3){
	// 		var msg = 'Error: unable to create websocket connection, please close 【Developer mode】 on the settings page';
	// 		layer.msg(msg,{time:5000})
	// 		if(Term.state === 3) return
	// 		Term.term.write(msg)
	// 		Term.state = 3;
	// 	}else{
	// 		console.log(ws_event)
	// 	}
	// },
	on_error: function (ws_event) {
		if (ws_event.target.readyState === 3) {
			if (Term.state === 3) return;
			Term.term.write(msg);
			Term.state = 3;
		} else {
			console.log(ws_event);
		}
	},

	//关闭连接
	close: function () {
		if (Term.bws) {
			Term.bws.close();
		}
	},

	resize: function () {
		setTimeout(function () {
			$('#term').height($('.term_box_all .layui-layer-content').height() - 18);
			Term.term.FitAddon.fit();
			Term.send(JSON.stringify({ resize: 1, rows: Term.term.rows, cols: Term.term.cols }));
			Term.term.focus();
		}, 100);
	},
	// resize: function() {
	//     var m_width = 100;
	//     var m_height = 34;
	//     Term.term.resize(m_width, m_height);
	//     Term.term.scrollToBottom();
	//     Term.term.focus();
	//     Term.send('new_terminal');
	// },

	//发送数据
	//@param event 唯一事件名称
	//@param data 发送的数据
	//@param collback 服务器返回结果时回调的函数,运行完后将被回收
	send: function (data, num) {
		//如果没有连接，则尝试连接服务器
		if (!Term.bws || Term.bws.readyState == 3 || Term.bws.readyState == 2) {
			Term.connect();
		}

		//判断当前连接状态,如果!=1，则100ms后尝试重新发送
		if (Term.bws.readyState === 1) {
			Term.bws.send(data);
		} else {
			if (Term.state === 3) return;
			if (!num) num = 0;
			if (num < 5) {
				num++;
				setTimeout(function () {
					Term.send(data, num++);
				}, 100);
			}
		}
	},
	// run: function (ssh_info) {
	//     var termCols = 100;
	//     var termRows = 34;
	//     var loadT = layer.msg('It is loading the files required by the terminal. Please wait...', { icon: 16, time: 0, shade: 0.3 });
	//     loadScript([
	//         "/static/build/xterm.min.js",
	//         "/static/build/addons/attach/attach.min.js",
	//         "/static/build/addons/fit/fit.min.js",
	//         "/static/build/addons/fullscreen/fullscreen.min.js",
	//         "/static/build/addons/search/search.min.js",
	//         "/static/build/addons/winptyCompat/winptyCompat.js"
	//     ], function () {
	//         layer.close(loadT);
	//         Term.term = new Terminal({ cols: termCols, rows: termRows, screenKeys: true, useStyle: true });
	//         Term.term.setOption('cursorBlink', true);
	//         Term.term_box = layer.open({
	//             type: 1,
	//             title: lan.public.terminal,
	//             area: ['920px', '630px'],
	//             closeBtn: 2,
	//             shadeClose: false,
	//             content: '<link rel="stylesheet" href="/static/build/xterm.min.css" />\
	// 					<link rel="stylesheet" href="/static/build/addons/fullscreen/fullscreen.min.css" />\
	//             <a class="btlink" onclick="show_ssh_login(1)" style="position: fixed;margin-left: 83px;margin-top: -30px;">[' + lan.public.set + ']</a>\
	//             <div class="term-box" style="background-color:#000"><div id="term"></div></div>',
	//             cancel: function () {
	//                 Term.term.destroy();
	//             },
	//             success: function () {
	//                 Term.term.open(document.getElementById('term'));
	//                 Term.resize();
	//             }
	//         });
	//         Term.term.on('data', function (data) {
	//             try {
	//                 Term.bws.send(data)
	//             } catch (e) {
	//                 Term.term.write('\r\nThe connection is lost and you are trying to reconnect!\r\n')
	//                 Term.connect()
	//             }
	//         });
	//         if (ssh_info) Term.ssh_info = ssh_info
	//         Term.connect();
	//     })

	// },
	run: function (ssh_info) {
		// if($("#panel_debug").attr("data") == 'True') {
		// 	layer.msg('Error: unable to create websocket connection, please close 【Developer mode】 on the settings page!',{icon:2,time:5000});
		// 	return;
		// }
		var loadT = layer.msg('It is loading the files required by the terminal. Please wait...', { icon: 16, time: 0, shade: 0.3 });
		loadScript(['/static/js/xterm.js'], function () {
			layer.close(loadT);
			Term.term = new Terminal({
				rendererType: 'canvas',
				cols: 100,
				rows: 31,
				fontSize: 15,
				screenKeys: true,
				useStyle: true,
			});
			Term.term.setOption('cursorBlink', true);
			Term.last_body = false;
			Term.term_box = layer.open({
				type: 1,
				title: lan.public.terminal,
				area: ['925px', '630px'],
				closeBtn: 2,
				shadeClose: false,
				skin: 'term_box_all',
				content:
					'<link rel="stylesheet" href="/static/css/xterm.css" />\
	            <div class="term-box" style="background-color:#000;padding-top: 7px;" id="term"></div>',
				cancel: function (index, lay) {
					bt.confirm(
						{
							msg: '<div style="word-break: break-word;">Closing the SSH session, the command in progress in the current command line session may be aborted. Continute?</div>',
							title: 'Cofirm to close the SSH session?',
						},
						function (ix) {
							Term.term.dispose();
							layer.close(index);
							layer.close(ix);
							Term.close();
						}
					);
					return false;
				},
				success: function () {
					$('.term_box_all').css('background-color', '#000');
					Term.term.open(document.getElementById('term'));
					Term.term.FitAddon = new FitAddon.FitAddon();
					Term.term.loadAddon(Term.term.FitAddon);
					Term.term.WebLinksAddon = new WebLinksAddon.WebLinksAddon();
					Term.term.loadAddon(Term.term.WebLinksAddon);
					Term.term.focus();
				},
			});
			Term.term.onData(function (data) {
				try {
					Term.bws.send(data);
				} catch (e) {
					Term.term.write('\r\nThe connection is lost and you are trying to reconnect!\r\n');
					Term.connect();
				}
			});
			if (ssh_info) Term.ssh_info = ssh_info;
			Term.connect();
		});
	},
	reset_login: function () {
		var ssh_info = {
			data: JSON.stringify({
				host: $("input[name='host']").val(),
				port: $("input[name='port']").val(),
				username: $("input[name='username']").val(),
				password: $("input[name='password']").val(),
			}),
		};
		$.post('/term_open', ssh_info, function (rdata) {
			if (rdata.status === false) {
				layer.msg(rdata.msg);
				return;
			}
			layer.closeAll();
			Term.connect();
			Term.term.scrollToBottom();
			Term.term.focus();
		});
	},
	localhost_login_form: function (result) {
		var template =
			'<div class="localhost-form-shade"><div class="localhost-form-view bt-form-2x"><div class="localhost-form-title"><i class="localhost-form_tip"></i><span style="vertical-align: middle;">Login failed, please fill the local server information!</span></div>\
        <div class="line input_group">\
            <span class="tname">Server IP</span>\
            <div class="info-r">\
                <input type="text" name="host" class="bt-input-text mr5" style="width:240px" placeholder="Server IP" value="127.0.0.1" autocomplete="off" />\
                <input type="text" name="port" class="bt-input-text mr5" style="width:60px" placeholder="Port" value="22" autocomplete="off"/>\
            </div>\
        </div>\
        <div class="line">\
            <span class="tname">SSH account</span>\
            <div class="info-r">\
                <input type="text" name="username" class="bt-input-text mr5" style="width:305px" placeholder="SSH account" value="root" autocomplete="off"/>\
            </div>\
        </div>\
        <div class="line">\
            <span class="tname">Verification</span>\
            <div class="info-r ">\
                <div class="btn-group">\
                    <button type="button" tabindex="-1" class="btn btn-sm auth_type_checkbox btn-success" data-ctype="0">Password</button>\
                    <button type="button" tabindex="-1" class="btn btn-sm auth_type_checkbox btn-default data-ctype="1">Server key</button>\
                </div>\
            </div>\
        </div>\
        <div class="line c_password_view show">\
            <span class="tname">Password</span>\
            <div class="info-r">\
                <input type="text" name="password" class="bt-input-text mr5" placeholder="SSH Password" style="width:305px;" value="" autocomplete="off"/>\
            </div>\
        </div>\
        <div class="line c_pkey_view hidden">\
            <span class="tname">Private key</span>\
            <div class="info-r">\
                <textarea rows="4" name="pkey" class="bt-input-text mr5" placeholder="SSH server key" style="width:305px;height: 80px;line-height: 18px;padding-top:10px;"></textarea>\
            </div>\
        </div><button type="submit" class="btn btn-sm btn-success">Login</button></div></div>';
		$('.term-box').after(template);
		$('.auth_type_checkbox').click(function () {
			var index = $(this).index();
			$(this).addClass('btn-success').removeClass('btn-default').siblings().removeClass('btn-success').addClass('btn-default');
			switch (index) {
				case 0:
					$('.c_password_view').addClass('show').removeClass('hidden');
					$('.c_pkey_view').addClass('hidden').removeClass('show').find('input').val('');
					break;
				case 1:
					$('.c_password_view').addClass('hidden').removeClass('show').find('input').val('');
					$('.c_pkey_view').addClass('show').removeClass('hidden');
					break;
			}
		});
		$('.localhost-form-view > button').click(function () {
			var form = {};
			$('.localhost-form-view input,.localhost-form-view textarea').each(function (index, el) {
				var name = $(this).attr('name'),
					value = $(this).val();
				form[name] = value;
				switch (name) {
					case 'port':
						if (!bt.check_port(value)) {
							bt.msg({ status: false, msg: 'Server port format error!' });
							return false;
						}
						break;
					case 'username':
						if (value == '') {
							bt.msg({ status: false, msg: 'Server user name cannot be empty!' });
							return false;
						}
						break;
					case 'password':
						if (value == '' && $('.c_password_view').hasClass('show')) {
							bt.msg({ status: false, msg: 'Server password cannot be empty!' });
							return false;
						}
						break;
					case 'pkey':
						if (value == '' && $('.c_pkey_view').hasClass('show')) {
							bt.msg({ status: false, msg: 'The server key cannot be empty!' });
							return false;
						}
						break;
				}
			});
			form.ps = 'Local server';

			if (result) {
				if (result.indexOf('@127.0.0.1') != -1) {
					var user = result.split('@')[0].split(',')[1];
					var port = result.split('1:')[1];
					$("input[name='username']").val(user);
					$("input[name='port']").val(port);
				}
			}
			var loadT = bt.load('Adding server information, please wait...');
			bt.send('create_host', 'xterm/create_host', form, function (res) {
				loadT.close();
				bt.msg(res);
				if (res.status) {
					bt.msg({ status: true, msg: 'Login successful!' });
					$('.layui-layer-shade').remove();
					$('.term_box_all').remove();
					Term.term.dispose();
					Term.close();
					web_shell();
				}
			});
		});
		$('.localhost-form-view [name="password"]')
			.keyup(function (e) {
				if (e.keyCode == 13) {
					$('.localhost-form-view > button').click();
				}
			})
			.focus();
	},
};

function web_shell() {
	Term.run();
}

socket = {
	emit: function (data, data2) {
		if (data === 'webssh') {
			data = data2;
		}
		if (typeof data === 'object') {
			return;
		}
		Term.send(data);
	},
};

function show_ssh_login(is_config) {
	if ($("input[name='ssh_user']").attr('autocomplete')) return;
	var s_body =
		'<div class="bt-form bt-form pd20 pb70">\
                            <style>.ssh_check_s1{    display: inline-block;\
    height: 38px;\
    background-color: #fff;\
    color: #050505;\
    white-space: nowrap;\
    text-align: center;\
    cursor: pointer;\
    border-radius: 0;\
    margin-left: 0px !important;\
    position: relative;\
    top: 2px;\
    line-height: 34px;\
    font-size: 13px;\
    border-color: #e6e6e6;\
    padding: 0 14px;\
    border: 1px solid #e0dfdf;}\
    .ssh_check_s2{margin-left: 0 !important;\
            position: relative;\
            top: 2px;\
            border-color: #e6e6e6;\
            display: inline - block;\
            height: 38px;\
            line-height: 38px;\
            padding: 0 18px;\
            background-color: #20a53a;\
            color: #fff;\
            white-space: nowrap;\
            text-align: center;\
            font-size: 14px;\
            border: none;\
            border-radius: 2px;\
            cursor: pointer;}        </style >\
                            <div class="line " style="margin-left: -40px;"><span class="tname">IP</span><div class="info-r "><input name="ssh_host" class="bt-input-text mr5" type="text" style="width:330px" value="127.0.0.1" autocomplete="off"></div></div>\
                            <div class="line " style="margin-left: -40px;"><span class="tname">Port</span><div class="info-r "><input name="ssh_port" class="bt-input-text mr5" type="text" style="width:330px" value="22" autocomplete="off"></div></div>\
                            <div class="line " style="margin-left: -40px;"><span class="tname">Username</span><div class="info-r "><input name="ssh_user" class="bt-input-text mr5" type="text" style="width:330px" value="root" readonly="readonly" autocomplete="off"></div></div>\
                            <div class="line " style="margin-left: -40px;"><span class="tname">Method</span><div class="info-r "><button class="ssh_check_s2" id="pass_check" onclick="pass_check()">Password</button><button id="rsa_check" class="ssh_check_s1" onclick="rsa_check()">Key</button></div></div>\
                            <div class="line ssh_passwd" style="margin-left: -40px;"><span class="tname">Password</span><div class="info-r "><input name="ssh_passwd" readonly="readonly" class="bt-input-text mr5" type="password" style="width:330px" value="" autocomplete="off"></div></div>\
                            <div class="line ssh_pkey" style="display:none;margin-left: -40px;"><span class="tname">Key</span><div class="info-r "><textarea name="ssh_pkey" class="bt-input-text mr5" style="width:330px;height:80px;" ></textarea></div></div>\
                            <div class="line " style="margin-left: -40px;"><span class="tname"></span><div class="info-r "><input style="margin-top: 1px;width: 16px;" name="ssh_is_save" id="ssh_is_save" class="bt-input-text mr5" type="checkbox" ><label style="position: absolute;margin-left: 5px;" for="ssh_is_save">Remember password, the next time you use the aaPanel terminal will automatically log in</label></div></div>\
                            <p style="color: red;margin-top: 10px;text-align: center;margin-left: -62px;">Only support login to this server</p>\
                            <div class="bt-form-submit-btn"><button type="button" class="btn btn-sm btn-danger" onclick="' +
		(is_config ? 'layer.close(ssh_login)' : 'layer.closeAll()') +
		'">Close</button><button type="button" class="btn btn-sm btn-success ssh-login" onclick="send_ssh_info()">' +
		(is_config ? 'Confirm' : 'Login SSH') +
		'</button></div></div>';
	ssh_login = layer.open({
		type: 1,
		title: is_config ? 'Please fill in the SSH connection configuration' : 'Please enter the SSH login account and password',
		area: '500px',
		closeBtn: 0,
		shadeClose: false,
		content: s_body,
	});

	setTimeout(function removeReadonly() {
		$("input[name='ssh_user']").removeAttr('readonly');
		$("input[name='ssh_passwd']").removeAttr('readonly');
		$("input[name='ssh_passwd']").focus();

		$("input[name='ssh_passwd']").keydown(function (e) {
			if (e.keyCode == 13) {
				$('.ssh-login').click();
			}
		});
	}, 500);
}

function pass_check() {
	$('#pass_check').attr('class', 'ssh_check_s2');
	$('#rsa_check').attr('class', 'ssh_check_s1');
	$('.ssh_pkey').hide();
	$('.ssh_passwd').show();
}

function rsa_check() {
	$('#pass_check').attr('class', 'ssh_check_s1');
	$('#rsa_check').attr('class', 'ssh_check_s2');
	$('.ssh_pkey').show();
	$('.ssh_passwd').hide();
}

function send_ssh_info() {
	pdata = {
		host: $("input[name='ssh_host']").val(),
		port: Number($("input[name='ssh_port']").val()),
		password: $("input[name='ssh_passwd']").val(),
		username: $("input[name='ssh_user']").val(),
		pkey: $("textarea[name='ssh_pkey']").val(),
	};
	if (pdata['host'] !== '127.0.0.1' && pdata['host'] !== 'localhost') {
		layer.msg('Connection address can only be [ 127.0.0.1 or localhost ]');
		$("input[name='ssh_host']").focus();
		return;
	}
	if (pdata['port'] < 1 || pdata['port'] > 65535) {
		layer.msg('Port range is incorrect [1-65535]');
		$("input[name='ssh_port']").focus();
		return;
	}
	if (!pdata['username']) {
		layer.msg('Username can not be empty!');
		$("input[name='ssh_user']").focus();
		return;
	}

	if ($('#rsa_check').attr('class') === 'ssh_check_s2') {
		pdata['c_type'] = 'True';
		if (!pdata['pkey']) {
			layer.msg('Private key cannot be empty!');
			$("input[name='ssh_pkey']").focus();
			return;
		}
	} else {
		if (!pdata['password']) {
			layer.msg('Password can not be blank!');
			$("input[name='ssh_passwd']").focus();
			return;
		}
	}
	if ($('#ssh_is_save').prop('checked')) {
		pdata['is_save'] = '1';
	}

	var loadT = layer.msg('Trying to log in to SSH...', { icon: 16, time: 0, shade: 0.3 });
	$.post('/term_open', { data: JSON.stringify(pdata) }, function () {
		layer.close(loadT);
		Term.send('reset_connect');
		layer.close(ssh_login);
		Term.term.focus();
	});
}

acme = {
	speed_msg: "<pre style='margin-bottom: 0px;height:250px;text-align: left;background-color: #000;color: #fff;white-space: pre-wrap;' id='create_lst'>[MSG]</pre>",
	loadT: null,
	//获取订单列表
	get_orders: function (callback) {
		acme.request(
			'get_orders',
			{},
			function (rdata) {
				callback(rdata);
			},
			'Getting order list...'
		);
	},
	//取指定订单
	get_find: function (index, callback) {
		acme.request(
			'get_order_find',
			{ index: index },
			function (rdata) {
				callback(rdata);
			},
			'Getting order information...'
		);
	},

	//下载指定证书包
	download_cert: function (index, callback) {
		acme.request(
			'update_zip',
			{ index: index },
			function (rdata) {
				if (!rdata.status) {
					bt.msg(rdata);
					return;
				}
				if (callback) {
					callback(rdata);
				} else {
					window.location.href = '/download?filename=' + rdata.msg;
				}
			},
			'Preparing to download..'
		);
	},

	//删除订单
	remove: function (index, callback) {
		acme.request('remove_order', { index: index }, function (rdata) {
			bt.msg(rdata);
			if (callback) callback(rdata);
		});
	},

	//吊销证书
	revoke: function (index, callback) {
		acme.request(
			'revoke_order',
			{ index: index },
			function (rdata) {
				bt.msg(rdata);
				if (callback) callback(rdata);
			},
			'Revoking certificate...'
		);
	},

	//验证域名(手动DNS申请)
	auth_domain: function (index, callback) {
		acme.show_speed_window('Verifying DNS...', function () {
			acme.request(
				'apply_dns_auth',
				{ index: index },
				function (rdata) {
					callback(rdata);
				},
				false
			);
		});
	},

	//取证书基本信息
	get_cert_init: function (pem_file, siteName, callback) {
		acme.request(
			'get_cert_init_api',
			{ pem_file: pem_file, siteName: siteName },
			function (cert_init) {
				callback(cert_init);
			},
			'Getting certificate information...'
		);
	},

	//显示进度
	show_speed: function () {
		bt.send(
			'get_lines',
			'ajax/get_lines',
			{
				num: 10,
				filename: '/www/server/panel/logs/letsencrypt.log',
			},
			function (rdata) {
				if ($('#create_lst').text() === '') return;
				if (rdata.status === true) {
					$('#create_lst').text(rdata.msg);
					$('#create_lst').scrollTop($('#create_lst')[0].scrollHeight);
				}
				setTimeout(function () {
					acme.show_speed();
				}, 1000);
			}
		);
	},

	//显示进度窗口
	show_speed_window: function (msg, callback) {
		acme.loadT = layer.open({
			title: false,
			type: 1,
			closeBtn: 0,
			shade: 0.3,
			area: '500px',
			offset: '30%',
			content: acme.speed_msg.replace('[MSG]', msg),
			success: function (layers, index) {
				setTimeout(function () {
					acme.show_speed();
				}, 1000);
				if (callback) callback();
			},
		});
	},

	//一键申请
	//domain 域名列表 []
	//auth_type 验证类型 model/http
	//auth_to 验证路径 网站根目录或dnsapi
	//auto_wildcard 是否自动组合通配符 1.是 0.否 默认0
	apply_cert: function (domains, auth_type, auth_to, auto_wildcard, callback) {
		acme.show_speed_window('Applying for a certificate...', function () {
			if (auto_wildcard === undefined) auto_wildcard = '0';
			pdata = {
				domains: JSON.stringify(domains),
				auth_type: auth_type,
				auth_to: auth_to,
				auto_wildcard: auto_wildcard,
			};

			if (acme.id) pdata['id'] = acme.id;
			if (acme.siteName) pdata['siteName'] = acme.siteName;
			acme.request(
				'apply_cert_api',
				pdata,
				function (rdata) {
					callback(rdata);
				},
				false
			);
		});
	},

	//续签证书
	renew: function (index, callback) {
		acme.show_speed_window('Renewing certificate...', function () {
			acme.request(
				'renew_cert',
				{ index: index },
				function (rdata) {
					callback(rdata);
				},
				false
			);
		});
	},

	//获取用户信息
	get_account_info: function (callback) {
		acme.request('get_account_info', {}, function (rdata) {
			callback(rdata);
		});
	},

	//设置用户信息
	set_account_info: function (account, callback) {
		acme.request('set_account_info', account, function (rdata) {
			bt.msg(rdata);
			if (callback) callback(rdata);
		});
	},

	//发送到请求
	request: function (action, pdata, callback, msg) {
		if (msg == undefined) msg = 'Processing, please wait...';
		if (msg) {
			var loadT = layer.msg(msg, { icon: 16, time: 0, shade: 0.3 });
		}
		$.post('/acme?action=' + action, pdata, function (res) {
			if (msg) layer.close(loadT);
			if (callback) callback(res);
		});
	},
};

/** 消息通道 **/
function MessageChannelSettings() {
	MessageChannel.get_channel_settings(function (rdata) {
		layer.open({
			type: 1,
			area: '600px',
			title: 'Setting up notification',
			skin: 'layer-channel-auth',
			closeBtn: 2,
			shift: 5,
			shadeClose: false,
			content:
				'<div class="bt-form">\
				<div class="bt-w-main">\
					<div class="bt-w-menu" style="width: 110px;">\
						<p class="bgw">Email</p>\
						<p>Telegram</p>\
					</div>\
					<div class="bt-w-con pd15" style="margin-left: 110px">\
						<div class="plugin_body">\
							<div class="conter_box active" >\
								<div class="bt-form">\
									<div class="line">\
										<button class="btn btn-success btn-sm" onclick="MessageChannel.add_receive_info()">Add recipient</button>\
										<button class="btn btn-default btn-sm" onclick="MessageChannel.sender_info_edit()">Sender settings</button>\
									</div>\
									<div class="line">\
										<div class="divtable">\
											<table class="table table-hover" width="100%" cellspacing="0" cellpadding="0" border="0"><thead><tr><th>Email</th><th width="80px">Operating</th></tr></thead></table>\
											<table class="table table-hover"><tbody id="receive_table"></tbody></table>\
										</div>\
									</div>\
								</div>\
							</div>\
							<div class="conter_box" style="display:none">\
                                <div class="line">\
                                    <span class="tname">ID</span>\
                                    <div class="info-r">\
                                        <input name="telegram_id" class="bt-input-text mr5" type="text" placeholder="Telegram ID" style="width: 300px" value="' +
				rdata.telegram.my_id +
				'">\
                                    </div>\
                                </div>\
                                <div class="line">\
                                    <span class="tname">TOKEN</span>\
                                    <div class="info-r">\
                                        <input name="telegram_token" class="bt-input-text mr5" type="text" placeholder="Telegram TOKEN" style="width: 300px" value="' +
				rdata.telegram.bot_token +
				'">\
                                    </div>\
                                </div>\
                                <div class="line">\
                                    <span class="tname"></span>\
                                    <button class="btn btn-success btn-sm addTelegram" style="margin-right: 10px;">Save</button>\
                                    ' +
				(rdata.telegram.setup ? '<button class="btn btn-default btn-sm delTelegram">Clear set</button>' : '') +
				'\
                                </div>\
                                <ul class="help-info-text c7" style="margin-top: 315px;">\
                                    <li>ID: Your telegram user ID</li>\
                                    <li>Token: Your telegram bot token </li>\
                                    <li>e.g: [ 12345677:AAAAAAAAA_a0VUo2jjr__CCCCDDD ] <a class="btlink" href="https://www.aapanel.com/forum/d/5115-how-to-add-telegram-to-panel-notifications" target="_blank" rel="noopener"> Help</a></li>\
                                </ul>\
							</div>\
						</div>\
					</div>\
				</div>\
				</div>',
			success: function () {
				$('.addTelegram').click(function () {
					var _id = $('[name=telegram_id]').val(),
						_token = $('[name=telegram_token]').val();
					if (_id == '' || _token == '') return layer.msg('input box cannot be empty!');
					var loadT = layer.msg('The notification is being generated, please wait...', { icon: 16, time: 0, shade: [0.3, '#000'] });
					$.post('/config?action=set_tg_bot', { bot_token: _token, my_id: _id }, function (rdata) {
						layer.close(loadT);
						layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
					});
				});
				$('.delTelegram').click(function () {
					var loadTs = layer.msg('Deleting notification, please wait...', { icon: 16, time: 0, shade: [0.3, '#000'] });
					$.post('/config?action=del_tg_info', function (rdata) {
						layer.close(loadTs);
						layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
						if (rdata.status) {
							$('[name=telegram_id]').val('');
							$('[name=telegram_token]').val('');
							$('.delTelegram').hide();
						}
					});
				});
			},
		});
		$('.bt-w-menu p').click(function () {
			var index = $(this).index();
			$(this).addClass('bgw').siblings().removeClass('bgw');
			$('.conter_box').eq(index).show().siblings().hide();
		});
		MessageChannel.get_receive_list();
	});
}
var MessageChannel = {
	//获取推送设置
	get_channel_settings: function (callback) {
		var loadT = layer.msg('Getting profile, please wait...', { icon: 16, time: 0, shade: [0.3, '#000'] });
		$.post('/config?action=get_settings2', function (rdata) {
			layer.close(loadT);
			if (callback) callback(rdata);
		});
	},
	// 获取收件者列表
	get_receive_list: function () {
		$.post('/config?action=get_settings2', function (rdata) {
			var _html = '',
				_list = rdata.user_mail.mail_list;
			if (_list.length > 0) {
				for (var i = 0; i < _list.length; i++) {
					_html +=
						'<tr>\
					<td>' +
						_list[i] +
						'</td>\
					<td width="80px" style="text-align:right;"><a onclick="MessageChannel.del_email(\'' +
						_list[i] +
						'\')" href="javascript:;" style="color:#20a53a">Del</a></td>\
					</tr>';
				}
			} else {
				_html = '<tr><td colspan="2">No Data</td></tr>';
			}
			$('#receive_table').html(_html);
		});
	},
	// 添加收件者
	add_receive_info: function () {
		var _this = this;
		layer.open({
			type: 1,
			area: '400px',
			title: 'Add recipient email',
			closeBtn: 2,
			shift: 5,
			shadeClose: false,
			content:
				'<div class="bt-form pd20 pb70">\
	        <div class="line">\
	            <span class="tname">Recipient mailbox</span>\
	            <div class="info-r">\
	                <input name="creater_email_value" class="bt-input-text mr5" type="text" style="width: 240px" value="">\
	            </div>\
	        </div>\
	        <div class="bt-form-submit-btn">\
	            <button type="button" class="btn btn-danger btn-sm smtp_closeBtn">Close</button>\
	            <button class="btn btn-success btn-sm CreaterReceive">Create</button>\
	        </div>\
	        </div>',
			success: function (layers, index) {
				$('.CreaterReceive').click(function () {
					var _receive = $('input[name=creater_email_value]').val();
					if (_receive != '') {
						var loadT = layer.msg('Please wait while creating recipient list...', { icon: 16, time: 0, shade: [0.3, '#000'] });
						layer.close(index);
						$.post('/config?action=add_mail_address', { email: _receive }, function (rdata) {
							layer.close(loadT);
							// 刷新收件列表
							_this.get_receive_list();
							layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
						});
					} else {
						layer.msg('Recipient mailbox cannot be empty！！', { icon: 2 });
					}
				});

				$('.smtp_closeBtn').click(function () {
					layer.close(index);
				});
			},
		});
	},
	// 删除收件者
	del_email: function (mail) {
		var loadT = layer.msg('Deleting[' + mail + '],please wait...', { icon: 16, time: 0, shade: [0.3, '#000'] }),
			_this = this;
		$.post('/config?action=del_mail_list', { email: mail }, function (rdata) {
			layer.close(loadT);
			layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
			_this.get_receive_list();
		});
	},
	// 设置发送者邮箱信息
	sender_info_edit: function () {
		var loadT = layer.msg('Getting profile, please wait...', { icon: 16, time: 0, shade: [0.3, '#000'] });
		$.post('/config?action=get_settings2', function (rdata) {
			layer.close(loadT);
			var qq_mail = rdata.user_mail.info.msg.qq_mail ? rdata.user_mail.info.msg.qq_mail : '',
				qq_stmp_pwd = rdata.user_mail.info.msg.qq_stmp_pwd ? rdata.user_mail.info.msg.qq_stmp_pwd : '',
				hosts = rdata.user_mail.info.msg.hosts ? rdata.user_mail.info.msg.hosts : '',
				port = rdata.user_mail.info.msg.port ? rdata.user_mail.info.msg.port : '',
				is_custom = $.inArray(port, ['25', '465', '587', '']) != -1; //是否自定义
			layer.open({
				type: 1,
				area: '460px',
				title: 'Set sender email information',
				closeBtn: 2,
				shift: 5,
				shadeClose: false,
				content:
					'<div class="bt-form pd20 pb70">\
        	<div class="line">\
                <span class="tname">Sender email</span>\
                <div class="info-r">\
                    <input name="channel_email_value" class="bt-input-text mr5" type="text" style="width: 300px" value="' +
					qq_mail +
					'">\
                </div>\
            </div>\
            <div class="line">\
                <span class="tname">SMTP password</span>\
                <div class="info-r">\
                    <input name="channel_email_password" class="bt-input-text mr5" type="password" style="width: 300px" value="' +
					qq_stmp_pwd +
					'">\
                </div>\
            </div>\
            <div class="line">\
                <span class="tname">SMTP server</span>\
                <div class="info-r">\
                    <input name="channel_email_server" class="bt-input-text mr5" type="text" style="width: 300px" value="' +
					hosts +
					'">\
                </div>\
            </div>\
            <div class="line">\
                <span class="tname">SMTP port</span>\
                <div class="info-r">\
                    <select class="bt-input-text mr5" id="port_select" style="width:' +
					(is_custom ? '300px' : '100px') +
					'"></select>\
                    <input name="channel_email_port" class="bt-input-text mr5" type="Number" style="display:' +
					(is_custom ? 'none' : 'inline-block') +
					'; width: 190px" value="' +
					port +
					'">\
                </div>\
            </div>\
            <ul class="help-info-text c7">\
            	<li>465 port is recommended, the protocol is SSL/TLS</li>\
            	<li>Port 25 is SMTP protocol, port 587 is STARTTLS protocol</li>\
            </ul>\
            <div class="bt-form-submit-btn">\
				' +
					(qq_mail != '' ? '<button type="button" class="btn btn-default btn-sm pull-left set_empty">Clear set</button>' : '') +
					'\
	            <button type="button" class="btn btn-danger btn-sm smtp_closeBtn">Close</button>\
	            <button class="btn btn-success btn-sm SetChannelEmail">Save</button></div>\
        	</div>',
				success: function (layers, index) {
					var _option = '';
					if (is_custom) {
						if (port == '465' || port == '') {
							_option = '<option value="465" selected="selected">465</option><option value="25">25</option><option value="587">587</option><option value="other">Customize</option>';
						} else if (port == '25') {
							_option = '<option value="465">465</option><option value="25" selected="selected">25</option><option value="587">587</option><option value="other">Customize</option>';
						} else {
							_option = '<option value="465">465</option><option value="25">25</option><option value="587" selected="selected">587</option><option value="other">Customize</option>';
						}
					} else {
						_option = '<option value="465">465</option><option value="25">25</option><option value="587" >587</option><option value="other" selected="selected">Customize</option>';
					}
					$('#port_select').html(_option);
					$('#port_select').change(function (e) {
						if (e.target.value == 'other') {
							$('#port_select').css('width', '100px');
							$('input[name=channel_email_port]').css('display', 'inline-block');
						} else {
							$('#port_select').css('width', '300px');
							$('input[name=channel_email_port]').css('display', 'none');
						}
					});
					$('.SetChannelEmail').click(function () {
						var _email = $('input[name=channel_email_value]').val();
						var _passW = $('input[name=channel_email_password]').val();
						var _server = $('input[name=channel_email_server]').val(),
							_port = '';
						if ($('#port_select').val() == 'other') {
							_port = $('input[name=channel_email_port]').val();
						} else {
							_port = $('#port_select').val();
						}
						if (!_email) return layer.msg('Email address cannot be empty!', { icon: 2 });
						if (!_passW) return layer.msg('STMP password cannot be empty!', { icon: 2 });
						if (!_server) return layer.msg('STMP server address cannot be empty!', { icon: 2 });
						if (!_port) return layer.msg('STMP server port cannot be empty!', { icon: 2 });

						var loadT = layer.msg('The notification is being generated, please wait...', { icon: 16, time: 0, shade: [0.3, '#000'] });
						$.post('/config?action=user_mail_send', { email: _email, stmp_pwd: _passW, hosts: _server, port: _port }, function (rdata) {
							layer.close(loadT);
							if (rdata.status) {
								layer.close(index);
								MessageChannel.get_channel_settings();
							}
							layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
						});
					});
					$('.smtp_closeBtn').click(function () {
						layer.close(index);
					});
					$('.set_empty').click(function () {
						var loadTs = layer.msg('notification, please wait...', { icon: 16, time: 0, shade: [0.3, '#000'] });
						$.post('/config?action=set_empty', { type: 'mail' }, function (rdata) {
							layer.close(loadTs);
							layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
							if (rdata.status) {
								layer.close(index);
							}
						});
					});
				},
			});
		});
	},
};
/** 消息通道 end**/
var product_recommend = {
	data: null,
	/**
	 * @description 初始化
	 */
	init: function (callback) {
		var _this = this;
		if (location.pathname.indexOf('bind') > -1) return;
		this.get_product_type(function (rdata) {
			_this.data = rdata;
			if (callback) callback(rdata);
		});
	},
	/**
	 * @description 获取推荐类型
	 * @param {object} type 参数{type:类型}
	 */
	get_recommend_type: function (type) {
		var config = null,
			pathname = location.pathname.replace('/', '') || 'home';
		for (var i = 0; i < this.data.length; i++) {
			var item = this.data[i];
			if (item.type == type && item.show) config = item;
		}
		return config;
	},

	/**
	 * @description 或指定版本事件
	 * @param {} name
	 */
	get_version_event: function (item, param) {
		var pay_status = this.get_pay_status();
		bt.soft.get_soft_find(item.name, function (res) {
			if ((res.type === 12 && pay_status.is_pay && pay_status.advanced !== 'ltd') || !pay_status.is_pay) {
				product_recommend.recommend_product_view(item);
			} else if (!res.setup) {
				bt.soft.install(item.name);
			} else {
				bt.plugin.get_plugin_byhtml(item.name, function (html) {
					if (typeof html === 'string') {
						layer.open({
							type: 1,
							shade: 0,
							skin: 'hide',
							content: html,
							success: function () {
								var is_event = false;
								for (var i = 0; i < item.eventList.length; i++) {
									var data = item.eventList[i];
									var oldVersion = data.version.replace('.', ''),
										newVersion = res.version.replace('.', '');
									if (newVersion <= oldVersion) {
										is_event = true;
										setTimeout(function () {
											new Function(data.event.replace('$siteName', param))();
										}, 100);
										break;
									}
								}
								if (!is_event) new Function(item.eventList[item.eventList.length - 1].event.replace('$siteName', param))();
							},
						});
					}
				});
			}
		});
	},
	/**
	 * @description 获取支付状态
	 */
	get_pay_status: function () {
		var pro_end = parseInt(bt.get_cookie('pro_end') || -1);
		var ltd_end = parseInt(bt.get_cookie('ltd_end') || -1);
		var is_pay = pro_end > -1 || ltd_end > -1; // 是否购买付费版本
		var advanced = 'pro'; // 已购买，专业版优先显示
		if (pro_end === -2 || pro_end > -1) advanced = 'pro';
		if (ltd_end === -2 || ltd_end > -1) advanced = 'ltd';
		var end_time = advanced === 'ltd' ? ltd_end : pro_end; // 到期时间
		return { advanced: advanced, is_pay: is_pay, end_time: end_time };
	},

	pay_product_sign: function (type, source) {
		switch (type) {
			case 'pro':
				bt.soft['updata_' + type](source);
				break;
			case 'ltd':
				bt.soft['updata_' + type](false, source);
				break;
		}
	},
	/**
	 * @description 获取项目类型
	 * @param {Function} callback 回调函数
	 */
	get_product_type: function (callback) {
		bt.send('get_pay_type', 'ajax/get_pay_type', {}, function (rdata) {
			bt.set_storage('session', 'get_pay_type', JSON.stringify(rdata));
			if (callback) callback(rdata);
		});
	},
	/**
	 * @description 推荐购买产品
	 * @param {Object} pay_id 购买的入口id
	 */
	recommend_product_view: function (config) {
		var name = config.name.split('_')[0];
		var status = this.get_pay_status();
		console.log(status);
		bt.open({
			title: false,
			area: '650px',
			btn: false,
			content:
				'<div class="ptb15" style="display: flex;">\
        <div class="product_view"><img src="/static/images/recommend/' +
				name +
				'.png"/></div>\
        <div class="product_describe ml10">\
          <div class="describe_title">' +
				config.pluginName +
				'</div>\
          <div class="describe_ps">' +
				config.ps +
				'</div>\
          <div class="product_describe_btn">\
            <a class="btn btn-default mr10 btn-sm productPreview ' +
				(!config.preview ? 'hide' : '') +
				'" href="' +
				config.preview +
				'" target="_blank">产品预览</a><button class="btn btn-success btn-sm buyNow">立即购买</button>\
          </div>\
        </div>\
      </div>',
			success: function () {
				// 产品预览
				$('.product_view img').click(function () {
					layer.open({
						type: 1,
						title: '查看图片',
						area: ['650px', '450px'],
						closeBtn: 2,
						btn: false,
						content: '<img src="/static/images/recommend/' + name + '.png" style="width:100%" />',
					});
				});
				// 立即购买
				$('.buyNow').click(function () {
					bt.set_cookie('pay_source', config.pay);
					bt.soft['updata_' + status.advanced]();
				});
			},
		});
	},
};

var rsa = {
	publicKey: null,
	/**
	 * @name 使用公钥加密
	 * @param {string} text
	 * @returns string
	 */
	encrypt_public: function (text) {
		this.publicKey = document.querySelector('.public_key').attributes.data.value;
		if (this.publicKey.length < 10) return text;
		var encrypt = new JSEncrypt();
		encrypt.setPublicKey(this.publicKey);
		return encrypt.encrypt(text);
	},
	/**
	 * @name 使用公钥解密
	 * @param {string} text
	 * @returns string
	 */
	decrypt_public: function (text) {
		this.publicKey = document.querySelector('.public_key').attributes.data.value;
		if (this.publicKey.length < 10) return null;
		var decrypt = new JSEncrypt();
		decrypt.setPublicKey(this.publicKey);
		return decrypt.decryptp(text);
	},
};

/**
 * @description 渲染邮箱配置视图
 */
function renderMailConfigView(data) {
	layer.open({
		type: 1,
		title: 'Set sender email information',
		area: ['470px', '376px'],
		btn: [lan.public.save, lan.public.cancel],
		skin: 'alert-send-view',
		content:
			'<div class="bt-form pd15">\
				<div class="line">\
						<span class="tname">Sender email</span>\
						<div class="info-r">\
								<input name="sender_mail_value" class="bt-input-text mr5" type="text" style="width: 300px">\
						</div>\
				</div>\
				<div class="line">\
						<span class="tname">SMTP password</span>\
						<div class="info-r">\
								<input name="sender_mail_password" class="bt-input-text mr5" type="password" style="width: 300px">\
						</div>\
				</div>\
				<div class="line">\
						<span class="tname">SMTP server</span>\
						<div class="info-r">\
								<input name="sender_mail_server" class="bt-input-text mr5" type="text" style="width: 300px">\
						</div>\
				</div>\
				<div class="line">\
						<span class="tname">SMTP port</span>\
						<div class="info-r">\
								<input name="sender_mail_port" class="bt-input-text mr5" type="text" style="width: 300px">\
						</div>\
				</div>\
				<ul class="help-info-text c7">\
						<li>465 port is recommended, the protocol is SSL/TLS</li>\
						<li>Port 25 is SMTP protocol, port 587 is STARTTLS protocol</li>\
				</ul>\
		</div>',
		success: function () {
			if (!$.isEmptyObject(data) && !$.isEmptyObject(data.data.send)) {
				var send = data.data.send,
					mail_ = send.qq_mail || '',
					stmp_pwd_ = send.qq_stmp_pwd || '',
					hosts_ = send.hosts || '',
					port_ = send.port || '';

				$('input[name=sender_mail_value]').val(mail_);
				$('input[name=sender_mail_password]').val(stmp_pwd_);
				$('input[name=sender_mail_server]').val(hosts_);
				$('input[name=sender_mail_port]').val(port_);
			} else {
				$('input[name=sender_mail_port]').val('465');
			}
		},
		yes: function (indexs) {
			var _email = $('input[name=sender_mail_value]').val(),
				_passW = $('input[name=sender_mail_password]').val(),
				_server = $('input[name=sender_mail_server]').val(),
				_port = $('input[name=sender_mail_port]').val();

			if (_email == '') return layer.msg('Email address cannot be empty!', { icon: 2 });
			if (_passW == '') return layer.msg('STMP password cannot be empty!', { icon: 2 });
			if (_server == '') return layer.msg('STMP server address cannot be empty!', { icon: 2 });
			if (_port == '') return layer.msg('STMP server port cannot be empty!', { icon: 2 });

			if (!data.setup) {
				bt_tools.send(
					{ url: '/config?action=install_msg_module&name=' + data.name, data: {} },
					function (res) {
						if (res.status) {
							bt_tools.send(
								{ url: '/config?action=set_msg_config&name=mail', data: { send: 1, qq_mail: _email, qq_stmp_pwd: _passW, hosts: _server, port: _port } },
								function (configM) {
									if (configM.status) {
										layer.close(indexs);
										layer.msg(configM.msg, {
											icon: configM.status ? 1 : 2,
										});
										if ($('.alert-view-box').length >= 0) $('.alert-view-box .tab-nav-border span:eq(1)').click();
									}
								},
								'Setting email Settings'
							);
						} else {
							layer.msg(res.msg, { icon: 2 });
						}
					},
					'Creating ' + data.title + ' module'
				);
			} else {
				bt_tools.send(
					{
						url: '/config?action=set_msg_config&name=mail',
						data: {
							send: 1,
							qq_mail: _email,
							qq_stmp_pwd: _passW,
							hosts: _server,
							port: _port,
						},
					},
					function (configM) {
						if (configM.status) {
							layer.close(indexs);
							layer.msg(configM.msg, {
								icon: configM.status ? 1 : 2,
							});
						}
					},
					'Setting email Settings'
				);
			}
		},
	});
}

/**
 * @description 渲染url通道方式视图
 */
function renderAlertUrlTypeChannelView(data) {
	var isEmpty = $.isEmptyObject(data.data);
	layer.open({
		type: 1,
		title: data['title'] + ' robot configuration',
		area: ['480px', '345px'],
		btn: [lan.public.save, lan.public.cancel],
		skin: 'alert-send-view',
		content:
			'<div class="pd15 bt-form">\
				<div class="line">\
					<span class="tname" style="width: 100px;">Name</span>\
					<div class="info-r" style="margin-left: 100px;">\
						<input type="text" name="chatName" value="' +
			(isEmpty ? '' : data.data.list.default.title) +
			'" class="bt-input-text mr10 " style="width:320px;" placeholder="Robot name or remarks" />\
					</div>\
				</div>\
				<div class="line">\
					<span class="tname" style="width: 100px;">URL</span>\
					<div class="info-r" style="margin-left: 100px;">\
						<textarea name="channel_url_value" class="bt-input-text mr5" type="text" placeholder="Please enter robot url" style="width: 320px; height:120px; line-height:20px; resize: none;"></textarea>\
					</div>\
					<ul class="help-info-text c7">\
						<li><a class="btlink" href="' +
			data.help +
			'" target="_blank">How to create the ' +
			data.title +
			' robot</a></li>\
					</ul>\
				</div>\
			</div>',
		success: function () {
			if (!$.isEmptyObject(data.data)) {
				var url = data['data'][data.name + '_url'] || '';
				$('textarea[name=channel_url_value]').val(url);
			}
		},
		yes: function (indexs) {
			var _index = $('.alert-view-box span.on').index();
			var _url = $('textarea[name=channel_url_value]').val(),
				_name = $('input[name=chatName]').val();
			if (_name == '') return layer.msg('Please enter the robot name or remarks', { icon: 2 });
			if (_url == '') return layer.msg('Please enter the robot url', { icon: 2 });
			if (!data.setup) {
				bt_tools.send(
					{ url: '/config?action=install_msg_module&name=' + data.name, data: {} },
					function (res) {
						if (res.status) {
							setTimeout(function () {
								bt_tools.send(
									{
										url: '/config?action=set_msg_config&name=' + data.name,
										data: {
											url: _url,
											title: _name,
											atall: 'True',
										},
									},
									function (rdata) {
										layer.close(indexs);
										layer.msg(rdata.msg, {
											icon: rdata.status ? 1 : 2,
										});
										if ($('.alert-view-box').length >= 0) {
											$('.alert-view-box .tab-nav-border span:eq(' + _index + ')').click();
										}
									},
									'Setting ' + data.title + ' configuration'
								);
							}, 100);
						} else {
							layer.msg(res.msg, { icon: 2 });
						}
					},
					'Creating ' + data.title + ' module'
				);
			} else {
				bt_tools.send(
					{
						url: '/config?action=set_msg_config&name=' + data.name,
						data: {
							url: _url,
							title: _name,
							atall: 'True',
						},
					},
					function (rdata) {
						layer.close(indexs);
						layer.msg(rdata.msg, {
							icon: rdata.status ? 1 : 2,
						});
						if ($('.alert-view-box').length >= 0) {
							$('.alert-view-box .tab-nav-border span:eq(' + _index + ')').click();
						}
					},
					'Setting ' + data.title + ' module'
				);
			}
		},
	});
}

function renderTelegramConfigView(data) {
	layer.open({
		type: 1,
		title: 'Telegram configuration',
		area: ['460px', '320px'],
		btn: [lan.public.save, lan.public.cancel],
		skin: 'alert-send-view',
		content:
			'<div class="pd15 bt-form">\
				<div class="line">\
					<span class="tname" style="width: 100px;">ID</span>\
					<div class="info-r" style="margin-left: 100px;">\
						<input type="text" name="telegram_id" class="bt-input-text " style="width: 280px;" placeholder="Telegram ID" />\
					</div>\
				</div>\
				<div class="line">\
					<span class="tname" style="width: 100px;">TOKEN</span>\
					<div class="info-r" style="margin-left: 100px;">\
						<input type="text" name="telegram_token" class="bt-input-text" type="text" style="width: 280px;" placeholder="Telegram TOKEN" />\
					</div>\
					<ul class="help-info-text c7" style="position: absolute; left: 40px; bottom: 20px;">\
						<li>ID: Your telegram user ID</li>\
						<li>Token: Your telegram bot token</li>\
						<li>e.g: [ 12345677:AAAAAAAAA_a0VUo2jjr__CCCCDDD ] <a class="btlink" href="https://www.aapanel.com/forum/d/5115-how-to-add-telegram-to-panel-notifications" target="_blank" rel="noopener">Help</a></li>\
					</ul>\
				</div>\
			</div>',
		success: function () {
			var res = data.data;
			if (res) {
				$('[name="telegram_id"]').val(res.my_id);
				$('[name="telegram_token"]').val(res.bot_token);
			}
		},
		yes: function (indexs) {
			var id = $('input[name=telegram_id]').val();
			var token = $('input[name=telegram_token]').val();
			var _index = $('.alert-view-box span.on').index();

			if (id == '') return layer.msg('Please enter Telegram ID!', { icon: 2 });
			if (token == '') return layer.msg('Please enter Telegram token', { icon: 2 });

			function saveConfig() {
				bt_tools.send(
					{
						url: '/config?action=set_msg_config&name=' + data.name,
						data: {
							my_id: id,
							bot_token: token,
						},
					},
					function (rdata) {
						layer.close(indexs);
						layer.msg(rdata.msg, {
							icon: rdata.status ? 1 : 2,
						});
						if ($('.alert-view-box').length >= 0) {
							$('.alert-view-box .tab-nav-border span:eq(' + _index + ')').click();
						}
					},
					'Setting ' + data.title + ' module'
				);
			}

			if (!data.setup) {
				bt_tools.send(
					{
						url: '/config?action=install_msg_module&name=' + data.name,
						data: {},
					},
					function (res) {
						if (res.status) {
							saveConfig();
						} else {
							layer.msg(res.msg, { icon: 2 });
						}
					},
					'Creating ' + data.title + ' module'
				);
			} else {
				saveConfig();
			}
		},
	});
}

// true: 消息推送 false: 消息通道
var ConfigIsPush = false;
// 消息推送弹框
var ConfigIndex = -1;

// 打开消息通道/消息推送
function open_three_channel_auth(stype) {
	var _title = 'Set Notification';
	var _area = '650px';
	var isPush = false;
	var assign = '';

	if (stype === 'MsgPush') {
		// 类型为消息推送
		_title = 'Set message push';
		_area = ['900px', '603px'];
		isPush = true;
	} else if (typeof stype != 'undefined' && stype) {
		// 指定选择消息通道的某个菜单
		assign = stype;
	}

	ConfigIsPush = isPush;

	ConfigIndex = layer.open({
		type: 1,
		area: _area,
		title: _title,
		closeBtn: 2,
		shift: 5,
		shadeClose: false,
		content:
			'\
		<div class="bt-form alarm-view">\
			<div class="bt-w-main" style="height: 560px;">\
				<div class="bt-w-menu" ' +
			(isPush ? 'style="width: 160px;"' : '') +
			'></div>\
				<div class="bt-w-con pd15" ' +
			(isPush ? 'style="margin-left: 160px;"' : '') +
			'>\
					<div class="plugin_body"></div>\
					<div class="plugin_update"></div>\
				</div>\
			</div>\
		</div>',
		success: function () {
			// 获取菜单配置
			getMsgConfig(assign ? assign : '');

			// 卸载/禁用模块
			$('.alarm-view').on('click', '.btn-uninstall', function () {
				uninstallMsgModuleConfig();
			});

			// 立即更新
			$('.alarm-view').on('click', '.btn-update', function () {
				installMsgModuleConfig();
			});
		},
	});
}

// 获取模板配置
function getTemplateMsgConfig(item, shtml) {
	$.post(
		'/' + (ConfigIsPush ? 'push' : 'config') + '?action=get_module_template',
		{
			module_name: item.name,
		},
		function (res) {
			if (res.status) {
				// 添加菜单内容
				$('.bt-w-main .plugin_body').html(res.msg.trim());
				// 添加底部内容
				var updateInfo = '';
				// 是否更新
				if (item.version !== item.info.version) {
					updateInfo = '【' + item['title'] + '】模块存在新的版本，为了不影响使用，请更新。<button class="btn btn-success btn-sm btn-update">立即更新</button>';
				}
				// $(".bt-w-main .plugin_update").html('\
				// <div class="box">\
				//   <div class="info">' + updateInfo + '</div>\
				//   <div><button class="btn btn-danger btn-sm btn-uninstall">卸载/禁用模块</button></div>\
				// </div>');
			} else {
				$('.bt-w-main .plugin_body').html(shtml);
			}
			new Function(item.name + '.init()')();
		}
	);
}

// 获取消息配置
function getMsgConfig(openType) {
	var _api = '/config?action=get_msg_configs';
	if (ConfigIsPush) _api = '/push?action=get_modules_list';

	$.post(_api, function (rdata) {
		var _menu = '';
		var menu_data = $('.alarm-view .bt-w-menu p.bgw').data('data');
		$('.alarm-view .bt-w-menu').html('');
		$.each(rdata, function (index, item) {
			var _default = item.data && item.data.default;
			var _flag = '';
			if (_default) {
				_flag = '<span class="show-default"></span>';
			}
			_menu = $("<p class='men_" + item['name'] + "'>" + item['title'] + _flag + '</p>').data('data', item);
			$('.alarm-view .bt-w-menu').append(_menu);
		});
		// $('.alarm-view .bt-w-menu').append('<a class="btlink update_list" onclick="refreshThreeChannelAuth()">更新列表</a>');
		$('.alarm-view .bt-w-menu p').click(function () {
			$(this).addClass('bgw').siblings().removeClass('bgw');
			var _item = $(this).data('data');

			var shtml =
				'<div class="plugin_user_info c7">\
        <p><b>名称：</b>' +
				_item.title +
				'</p>\
        <p><b>版本：</b>' +
				_item.version +
				'</p>\
        <p><b>时间：</b>' +
				_item.date +
				'</p>\
        <p><b>描述：</b>' +
				_item.ps +
				'</p>\
        <p><b>说明：</b><a class="btlink" href="' +
				_item.help +
				'" target=" _blank">' +
				_item.help +
				'</a></p>\
        <p><button class="btn btn-success btn-sm mt1" onclick="installMsgModuleConfig(\'' +
				_item.name +
				'\')">安装模块</button></p>\
      </div>';
			if (_item['setup']) {
				getTemplateMsgConfig(_item, shtml);
			} else {
				$('.bt-w-main .plugin_body').html(shtml);
				$('.bt-w-main .plugin_update').html('');
			}
		});
		if (menu_data) {
			$('.men_' + menu_data['name']).click();
		} else {
			if (typeof openType != 'undefined' && openType) {
				$('.alarm-view .bt-w-menu p.men_' + openType).trigger('click');
			} else {
				$('.alarm-view .bt-w-menu p').eq(0).trigger('click');
			}
		}
	});
}

function installMsgModuleConfig(name) {
	var _api = '/config?action=install_msg_module';
	if (ConfigIsPush) _api = '/push?action=install_module';
	name = name ? '.men_' + name : '';
	var _item = $('.alarm-view .bt-w-menu p.bgw' + name).data('data');
	var spt = '安装';
	if (_item.setup) spt = '更新';

	layer.confirm(
		'是否要' + spt + '【' + _item.title + '】模块',
		{
			title: '安装模块',
			closeBtn: 2,
			icon: 0,
		},
		function () {
			var loadT = layer.msg('正在' + spt + _item.title + '模块中,请稍候...', {
				icon: 16,
				time: 0,
				shade: [0.3, '#000'],
			});
			$.post(_api + '&name=' + _item.name + '', function (res) {
				getMsgConfig();
				layer.close(loadT);
				layer.msg(res.msg, {
					icon: res.status ? 1 : 2,
				});
			});
		}
	);
}

function uninstallMsgModuleConfig() {
	var _api = '/config?action=uninstall_msg_module';
	if (ConfigIsPush) _api = '/push?action=uninstall_module';

	var _item = $('.alarm-view .bt-w-menu p.bgw').data('data');

	layer.confirm(
		'是否确定要卸载【' + _item.title + '】模块',
		{
			title: '卸载模块',
			closeBtn: 2,
			icon: 0,
		},
		function () {
			var loadT = layer.msg('正在卸载' + _item.title + '模块中,请稍候...', {
				icon: 16,
				time: 0,
				shade: [0.3, '#000'],
			});
			$.post(_api + '&name=' + _item.name + '', function (res) {
				layer.close(loadT);
				getMsgConfig();
				layer.msg(res.msg, {
					icon: res.status ? 1 : 2,
				});
			});
		}
	);
}

function refreshThreeChannelAuth() {
	var _api = '/config?action=get_msg_configs';
	if (ConfigIsPush) _api = '/push?action=get_modules_list';

	var loadT = layer.msg('正在更新模块列表中,请稍候...', {
		icon: 16,
		time: 0,
		shade: [0.3, '#000'],
	});
	layer.confirm(
		'是否确定获取最新的模块列表',
		{
			title: '刷新列表',
			closeBtn: 2,
			icon: 0,
		},
		function (index) {
			layer.close(index);
			layer.close(ConfigIndex);
			$.post(
				_api,
				{
					force: 1,
				},
				function (rdata) {
					layer.close(loadT);
					open_three_channel_auth(ConfigIsPush ? 'MsgPush' : '');
				}
			);
		}
	);
}
