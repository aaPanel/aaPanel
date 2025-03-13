// bt.pub.check_install(function (rdata) {
//     if (rdata === false) bt.index.rec_install();
// })
$("select[name='network-io']").change(function () {
	var net_key = $(this).val();
	if (net_key == 'all') net_key = '';
	bt.set_cookie('network_io_key', net_key);
});
$("select[name='network-io'],select[name='disk-io']").change(function () {
	var key = $(this).val(),
		type = $(this).attr('name');
	if (type == 'network-io') {
		if (key == 'all') key = '';
		bt.set_cookie('network_io_key', key);
	} else {
		bt.set_cookie('disk_io_key', key);
	}
});
$('.tabs-nav span').click(function () {
	var indexs = $(this).index();
	$(this).addClass('active').siblings().removeClass('active');
	$('.tabs-content .tabs-item:eq(' + indexs + ')')
		.addClass('tabs-active')
		.siblings()
		.removeClass('tabs-active');
	$('.tabs-down select:eq(' + indexs + ')')
		.removeClass('hide')
		.siblings()
		.addClass('hide');
	switch (indexs) {
		case 0:
			index.net.table.resize();
			break;
		case 1:
			index.iostat.table.resize();
			break;
	}
});
var interval_stop = false;
var index = {
	warning_list: [],
	warning_num: 0,
	warning_list: [],
	warning_num: 0,
	series_option: {}, // 配置项
	chart_json: {}, // 所有图表echarts对象
	chart_view: {}, // 磁盘echarts对象
	disk_view: [], // 释放内存标记
	chart_result: null,
	release: false,
	load_config: [
		{
			title: lan.index.run_block,
			val: 90,
			color: '#dd2f00',
		},
		{
			title: lan.index.run_slow,
			val: 80,
			color: '#ff9900',
		},
		{
			title: lan.index.run_normal,
			val: 70,
			color: '#20a53a',
		},
		{
			title: lan.index.run_fluent,
			val: 30,
			color: '#20a53a',
		},
	],
	interval: {
		limit: 10,
		count: 0,
		task_id: 0,
		start: function () {
			var _this = this;
			_this.count = 0;
			_this.task_id = setInterval(function () {
				if (_this.count >= _this.limit) {
					_this.reload();
					return;
				}
				_this.count++;
				if (!interval_stop) index.reander_system_info();
			}, 3000);
		},
		reload: function () {
			var _this = this;
			if (_this) clearInterval(_this.task_id);
			_this.start();
		},
	},
	net: {
		table: null,
		data: {
			uData: [],
			dData: [],
			aData: [],
		},
		init: function () {
			//流量图表
			index.net.table = echarts.init(document.getElementById('NetImg'));
			var obj = {};
			obj.dataZoom = [];
			obj.unit = lan.index.unit + ':KB/s';
			obj.tData = index.net.data.aData;

			obj.list = [];
			obj.list.push({
				name: lan.index.net_up,
				data: index.net.data.uData,
				circle: 'circle',
				itemStyle: { normal: { color: '#f7b851' } },
				areaStyle: {
					normal: {
						color: new echarts.graphic.LinearGradient(
							0,
							0,
							0,
							1,
							[
								{ offset: 0, color: 'rgba(255, 140, 0,1)' },
								{ offset: 1, color: 'rgba(255, 140, 0,.4)' },
							],
							false
						),
					},
				},
				lineStyle: { normal: { width: 1, color: '#f7b851' } },
			});
			obj.list.push({
				name: lan.index.net_down,
				data: index.net.data.dData,
				circle: 'circle',
				itemStyle: { normal: { color: '#52a9ff' } },
				areaStyle: {
					normal: {
						color: new echarts.graphic.LinearGradient(
							0,
							0,
							0,
							1,
							[
								{ offset: 0, color: 'rgba(30, 144, 255,1)' },
								{ offset: 1, color: 'rgba(30, 144, 255,.4)' },
							],
							false
						),
					},
				},
				lineStyle: { normal: { width: 1, color: '#52a9ff' } },
			});
			option = bt.control.format_option(obj);

			index.net.table.setOption(option);
			window.addEventListener('resize', function () {
				index.net.table.resize();
			});
		},
		add: function (up, down) {
			var _net = this;
			var limit = 8;
			var d = new Date();

			if (_net.data.uData.length >= limit) _net.data.uData.splice(0, 1);
			if (_net.data.dData.length >= limit) _net.data.dData.splice(0, 1);
			if (_net.data.aData.length >= limit) _net.data.aData.splice(0, 1);

			_net.data.uData.push(up);
			_net.data.dData.push(down);
			_net.data.aData.push(d.getHours() + ':' + d.getMinutes() + ':' + d.getSeconds());
		},
	},
	iostat: {
		table: null,
		data: {
			uData: [],
			dData: [],
			aData: [],
			tipsData: [],
		},
		init: function () {
			//流量图表
			index.iostat.table = echarts.init(document.getElementById('IoStat'));
			var obj = {};
			obj.dataZoom = [];
			obj.unit = lan.index.unit + ':MB/s';
			obj.tData = index.iostat.data.aData;
			obj.formatter = function (config) {
				var _config = config,
					_tips = 'Time：' + _config[0].axisValue + '<br />',
					options = {
						read_bytes: 'Read Bytes',
						read_count: 'Read Count ',
						read_merged_count: 'Read Merged Count',
						read_time: 'Read Wait',
						write_bytes: 'Write Bytes',
						write_count: 'Write Count',
						write_merged_count: 'Write Merged Count',
						write_time: 'Write Wait',
					},
					data = index.iostat.data.tipsData[config[0].dataIndex],
					list = ['read_count', 'write_count', 'read_merged_count', 'write_merged_count', 'read_time', 'write_time'];
				for (var i = 0; i < config.length; i++) {
					if (typeof config[i].data == 'undefined') return false;
					_tips +=
						'<span style="display: inline-block;width: 10px;height: 10px;border-radius: 50%;background: ' +
						config[i].color +
						';"></span>&nbsp;&nbsp;<span>' +
						config[i].seriesName +
						'：' +
						parseFloat(config[i].data).toFixed(2) +
						' MB/s' +
						'</span><br />';
				}
				$.each(list, function (index, item) {
					_tips +=
						'<span style="display: inline-block;width: 10px;height: 10px;"></span>&nbsp;&nbsp;<span style="' +
						(item.indexOf('time') > -1 ? 'color:' + (data[item] > 100 && data[item] < 1000 ? '#ff9900' : data[item] >= 1000 ? 'red' : '#20a53a') : '') +
						'">' +
						options[item] +
						'：' +
						data[item] +
						(item.indexOf('time') > -1 ? ' ms' : ' per sec') +
						'</span><br />';
				});
				return _tips;
			};
			obj.list = [];
			obj.list.push({
				name: 'Read Bytes',
				data: index.iostat.data.uData,
				circle: 'circle',
				itemStyle: { normal: { color: '#FF4683' } },
				areaStyle: {
					normal: {
						color: new echarts.graphic.LinearGradient(
							0,
							0,
							0,
							1,
							[
								{ offset: 0, color: 'rgba(255,70,131,1)' },
								{ offset: 1, color: 'rgba(255,70,131,.4' },
							],
							false
						),
					},
				},
				lineStyle: { normal: { width: 1, color: '#FF4683' } },
			});
			obj.list.push({
				name: 'Write Bytes',
				data: index.iostat.data.dData,
				circle: 'circle',
				itemStyle: { normal: { color: '#6CC0CF' } },
				areaStyle: {
					normal: {
						color: new echarts.graphic.LinearGradient(
							0,
							0,
							0,
							1,
							[
								{ offset: 0, color: 'rgba(108,192,207,1)' },
								{ offset: 1, color: 'rgba(108,192,207,.4)' },
							],
							false
						),
					},
				},
				lineStyle: { normal: { width: 1, color: '#6CC0CF' } },
			});
			option = bt.control.format_option(obj);
			index.iostat.table.setOption(option);
			window.addEventListener('resize', function () {
				index.iostat.table.resize();
			});
		},
		add: function (read, write, data) {
			var _disk = this;
			var limit = 8;
			var d = new Date();
			if (_disk.data.uData.length >= limit) _disk.data.uData.splice(0, 1);
			if (_disk.data.dData.length >= limit) _disk.data.dData.splice(0, 1);
			if (_disk.data.aData.length >= limit) _disk.data.aData.splice(0, 1);
			if (_disk.data.tipsData.length >= limit) _disk.data.tipsData.splice(0, 1);
			_disk.data.uData.push(read);
			_disk.data.dData.push(write);
			_disk.data.tipsData.push(data);
			_disk.data.aData.push(d.getHours() + ':' + d.getMinutes() + ':' + d.getSeconds());
		},
	},
	mem: {
		status: 1,
		set_status: function (obj, status, val) {
			var _this = this;
			_this.status = status;
			var _div = $('<div><span style="display:none">1</span></div>');
			if (status == 2) {
				obj.find('.mem-re-con').animate({ top: '-400px', opacity: 0 }); //动画
				var btlen = parseInt(obj.find('.occupy span').html());
				for (var i = 0; i < btlen; i++) {
					setTimeout(index.set_val(obj.parents('li'), { usage: btlen - i }), i * 30);
				}
				obj.addClass('mem-action');
				obj.find('.occupy').html(_div.append(lan.index.memre_ok_0 + ' <img src="/static/img/ings.gif">').html());
			} else if (status == 1) {
				//完成
				obj.removeClass('mem-action');
				obj
					.find('.occupy')
					.removeClass('line')
					.html('<span>' + val + '</span>%');
			} else {
				obj.find('.occupy').html(_div.append(status).html());
				if (bt.contains(status, '<br>')) obj.find('.occupy').addClass('line');
			}
		},
	},
	get_init: function () {
		var _this = this;
		// setTimeout(function () { _this.get_disk_list(); }, 10);
		setTimeout(function () {
			_this.get_warning_list();
		}, 20);
		// setTimeout(function () { _this.get_server_info(); }, 30);
		_this.reander_system_info(function (rdata) {
			// 负载悬浮事件
			$('#loadChart').hover(
				function () {
					var arry = [
						[lan.index.avg_load_atlast_onemin, rdata.load.one],
						[lan.index.avg_load_atlast_fivemin, rdata.load.five],
						[lan.index.avg_load_atlast_fifteenmin, rdata.load.fifteen],
					],
						tips = '';
					$.each(arry || [], function (index, item) {
						tips += item[0] + '：' + item[1] + '</br>';
					});
					$.each(rdata.cpu_times || {}, function (key, item) {
						tips += key + '：' + item + '</br>';
					});
					// '最近1分钟平均负载：' + rdata.load.one + '</br>最近5分钟平均负载：' + rdata.load.five + '</br>最近15分钟平均负载：' + rdata.load.fifteen + ''
					layer.tips(tips, this, { time: 0, tips: [1, '#999'] });
				},
				function () {
					layer.closeAll('tips');
				}
			);

			// cpu悬浮事件
			$('#cpuChart').hover(
				function () {
					var cpuText = '';
					for (var i = 1; i < rdata.cpu[2].length + 1; i++) {
						var cpuUse = parseFloat(rdata.cpu[2][i - 1] == 0 ? 0 : rdata.cpu[2][i - 1]).toFixed(1);
						if (i % 2 != 0) {
							cpuText += 'CPU-' + i + '：' + cpuUse + '%&nbsp;|&nbsp;';
						} else {
							cpuText += 'CPU-' + i + '：' + cpuUse + '%';
							cpuText += `\n`;
						}
					}

					layer.tips(rdata.cpu[3] + '</br>' + rdata.cpu[5] + ' CPU，' + rdata.cpu[4] + ' Physical core, ' + rdata.cpu[1] + ' Logical core</br>' + cpuText, this, { time: 0, tips: [1, '#999'] });
				},
				function () {
					layer.closeAll('tips');
				}
			);

			$('#memChart')
				.hover(
					function () {
						$(this).append('<div class="mem_mask shine_green" title="Click to free RAM"><div class="men_inside_mask"></div><div class="mem-re-con" style="display:block"></div></div>');
						$(this).find('.mem_mask .mem-re-con').animate({ top: '5px' }, 400);
						$(this).next().hide();
					},
					function () {
						$(this).find('.mem_mask').remove();
						$(this).next().show();
					}
				)
				.click(function () {
					var that = $(this);
					var data = _this.chart_result.mem;
					bt.show_confirm(lan.index.mem_release_sure, '<font style="color:red;">' + lan.index.mem_release_warn + '</font>', function () {
						_this.release = true;
						var option = JSON.parse(JSON.stringify(_this.series_option));
						// 释放中...
						var count = '';
						var setInter = setInterval(function () {
							if (count == '...') {
								count = '.';
							} else {
								count += '.';
							}
							option.series[0].detail.formatter = lan.index.memre_ok_0 + count;
							option.series[0].detail.fontSize = 15;
							option.series[0].data[0].value = 0;
							_this.chart_view.mem.setOption(option, true);
							that.next().hide();
						}, 400);
						// 释放接口请求
						bt.system.re_memory(function (res) {
							that.next().show();
							clearInterval(setInter);
							option.series[0].detail = $.extend(option.series[0].detail, {
								formatter: lan.index.memre_ok_1 + '\n' + bt.format_size(data.memRealUsed - res.memRealUsed),
								lineHeight: 18,
								padding: [5, 0],
							});
							_this.chart_view.mem.setOption(option, true);
							setTimeout(function () {
								_this.release = false;
								_this.chart_result.mem = res;
								_this.chart_active('mem');
							}, 2000);
						});
					});
				});

			// 磁盘悬浮事件
			// for(var i = 0; i < rdata.disk.length; i++){
			//     var disk = rdata.disk[i],texts = "<strong>"+lan.index.base_info+"</strong></br>"
			//     texts += "Partition: " + disk.filesystem + "</br>"
			//     texts += "Type: " + disk.type + "</br>"
			//     texts += "Mount point: " + disk.path + "</br></br>"
			//     texts += "<strong>"+ lan.index.inode_info +":</strong></br>"
			//     texts += lan.index.total+": " + disk.inodes[0] + "</br>"
			//     texts += lan.index.already_use+": " + disk.inodes[1] + "</br>"
			//     texts += lan.index.available+": " + disk.inodes[2] + "</br>"
			//     texts += lan.index.inode_percent+": " + disk.inodes[3] + "</br></br>"
			//     texts += "<strong>"+lan.index.capacity_info+"</strong></br>"
			//     texts += lan.index.capacity+": " + disk.size[0] + "</br>"
			//     texts += lan.index.already_use+": " + disk.size[1] + "</br>"
			//     texts += lan.index.available+": " + disk.size[2] + "</br>"
			//     texts += lan.index.usage_rate+": " + disk.size[3] + "</br>"
			//     $("#diskChart" + i).data('title',texts).hover(function () {
			//         layer.tips($(this).data('title'), this, { time: 0, tips: [1, '#999'] });
			//     }, function(){
			//         layer.closeAll('tips');
			//     })
			// }
			var is_remove_disk = [],
				idx = 0,
				taskStatus = []; //扫描状态
			for (var i = 0; i < rdata.disk.length; i++) {
				is_remove_disk.push(true);
				taskStatus.push(false);
				var mouseX = 0,
					mouseY = 0;
				$(document).mousemove(function (e) {
					mouseY = e.pageY;
					mouseX = e.pageX;
				});
				var diskInterval = null;
				$('#diskChart' + i)
					.data('disk', rdata.disk[i])
					.hover(
						function () {
							var disk = $(this).data('disk');
							clearInterval(diskInterval);
							var top = $(this).offset().top,
								left = $(this).offset().left,
								used_size = parseFloat(disk.size[3].substring(0, disk.size[3].lastIndexOf('%')));
							idx = $(this).prop('id').replace('diskChart', '');
							for (var i = 0; i < is_remove_disk.length; i++) {
								if (i !== parseInt(idx) && is_remove_disk[i]) {
									$('.disk_scanning_tips' + i).remove();
								}
							}
							if (!$('.disk_scanning_tips' + idx).length) {
								layer.open({
									type: 1,
									closeBtn: 1,
									shade: 0,
									area: '320px',
									title: false,
									skin: 'disk_scanning_tips disk_scanning_tips' + idx,
									content:
										'<div class="pd20 disk_scanning" data-index="' +
										idx +
										'">\
															<div class="disk_cont">\
																<div class="disk-title">\
																	Disk space: <div class="' +
										(used_size >= 80 ? (used_size >= 90 ? 'bg-red' : 'bg-org') : 'bg-green') +
										'">' +
										(used_size >= 80 ? 'Lack' : 'Plenty') +
										'</div>\
																	<button type="button" data-path="' +
										disk.path +
										'" title="Clean up now" class="btn btn-success disk_scanning_btn">Clean up now</button></div>\
																<div class="disk-item-list active">\
																	<div class="disk-item-header">\
																		<div class="disk-header-title">Basic information</div>\
																	</div>\
																	<div class="disk-item-body">\
																		<div class="disk-body-list">Type：' +
										disk.type +
										'</div>\
																		<div class="disk-body-list more_wrap"><div>Mount point：</div><div>' +
										disk.path +
										'</div></div>\
																		<div class="disk-body-list"><div class="progressBar"><span style="left: ' +
										(used_size < 12 ? used_size + 2 : used_size - 11) +
										'%;' +
										(used_size < 12 ? 'color:#666;' : '') +
										'">' +
										disk.size[3] +
										'</span><div style="width: ' +
										disk.size[3] +
										'; ' +
										(used_size === 100 ? 'border-radius: 2px;' : '') +
										'" class="progress ' +
										(used_size >= 80 ? (used_size >= 90 ? 'bg-red' : 'bg-org') : 'bg-green') +
										'"></div></div></div>\
																		<div class="disk-body-list use_disk" style="margin-top: 6px;white-space: pre-line;">Available：' +
										parseFloat(disk.size[2]) +
										' ' +
										disk.size[2].replace(parseFloat(disk.size[2]), '') +
										'，Total：' +
										parseFloat(disk.size[0]) +
										' ' +
										disk.size[0].replace(parseFloat(disk.size[0]), '') +
										'\n Used：' +
										parseFloat(disk.size[1]) +
										' ' +
										disk.size[1].replace(parseFloat(disk.size[1]), '') +
										'，System：' +
										disk.size[4] +
										'</div>\
																		</div>\
																</div>\
																<hr />\
																<div class="disk-item-list active">\
																	<div class="disk-item-header">\
																		<div class="disk-header-title">Other information</div>\
																	</div>\
																	<div class="disk-item-body">\
																		<div class="disk-body-list more_wrap"><div>File system：</div><div>' +
										disk.filesystem +
										'</div></div>\
																		<div class="disk-body-list inodes0">Total Inodes：' +
										disk.inodes[0] +
										'</div>\
																		<div class="disk-body-list inodes1">Used Inode：' +
										disk.inodes[1] +
										'</div>\
																		<div class="disk-body-list inodes2">Available Inode：' +
										disk.inodes[2] +
										'</div>\
																		<div class="disk-body-list inodes3">Usage Inode：' +
										disk.inodes[3] +
										'</div>\
																	</div>\
																</div>\
															</div>\
															<div class="disk_scan_cont hide">\
																<div class="disk-scan-header">\
																	<button type="button" title="后退" class="btn btn-default disk_back_btn" data-index="' +
										idx +
										'" ><span class="disk_back_icon"></span><span>后退</span></button>\
																	<div>磁盘扫描</div>\
																</div>\
																<div class="disk-scan-view hide">\
																	<pre id="scanProgress">正在获取扫描日志</pre>\
																</div>\
																<div class="disk-file-view hide">\
																<div class="disk-file-load" style="position:absolute;width: 100%;height: 100%;top: 0;left:0;display: none;z-index: 99999999;background:rgba(0,0,0,0.3);align-items:center;justify-content: center;">\
																		<div class="pd15" style="background: #fff;">\
																			<img src="/static/img/loading.gif" class="mr10">\
																			<span>正在获取文件信息，请稍后...</span>\
																		</div>\
																	</div>\
																	<div class="filescan-nav" id="fileScanPath"></div>\
																	<div class="filescan-list" id="fileScanTable">\
																		<div class="filescan-list-title">\
																			<div class="filescan-list-title-item text-left">文件名</div>\
																			<div class="filescan-list-title-item">大小</div>\
																			<div class="filescan-list-title-item text-right">操作</div>\
																		</div>\
																		<div class="filescan-list-body"></div>\
																	</div>\
																</div>\
															</div>\
														</div>',
									success: function (layero, index) {
										is_remove_disk[idx] = true;
										// $(layero).find('.layui-layer-close2').addClass('layui-layer-close1').removeClass('layui-layer-close2');
										$(layero).find('.layui-layer-close2').remove();
										$(layero).css({
											top: top + 140 - $(window).scrollTop() + 'px',
											left: left - 160,
										});
										$(window).resize(function () {
											for (var i = 0; i < is_remove_disk.length; i++) {
												if ($('.disk_scanning_tips' + i).length) {
													$('.disk_scanning_tips' + i).css({
														top: $('#diskChart' + i).offset().top + 140 - $(window).scrollTop() + 'px',
														left: $('#diskChart' + i).offset().left - 160,
													});
												}
											}
										});
										$(window).scroll(function () {
											$(layero).css({
												top: $('#diskChart' + idx).offset().top + 140 - $(window).scrollTop() + 'px',
												left: $('#diskChart' + idx).offset().left - 160,
											});
										});
										var id = null, // 扫描id
											taskPath = '', // 扫描目录
											taskList = {}; // 扫描缓存列表
										//展示收起
										// $(layero).find('.disk-item-header').on('click', function () {
										//   if ($(this).parent().hasClass('active')) {
										//     $(this).parent().removeClass('active');
										//     $(this).find('span').text('展示');
										//     $(this).find('img').removeAttr('style');
										//   } else {
										//     $(this).parent().addClass('active');
										//     $(this).find('span').text('收起');
										//     $(this).find('img').css('transform', 'rotate(180deg)');
										//   }
										// })

										// 后退
										$(layero)
											.find('.disk_back_btn')
											.on('click', function () {
												var path = $(this).data('path'),
													index = $(this).data('index');
												if (path !== undefined && path !== 'undefined') {
													if (path === '') {
														$(layero).find('.filescan-nav-item.present').click();
														$(this).data('path', 'undefined');
													} else {
														var rdata = taskList[path.replace('//', '/')];
														renderFilesTable(rdata, path); // 渲染文件表格
														renderFilesPath(path); // 渲染文件路径
													}
												} else {
													if (taskStatus[index]) {
														layer.confirm(
															'取消扫描，将会中断当前扫描目录进程，是否继续？',
															{
																title: '取消扫描',
																closeBtn: 2,
																icon: 3,
															},
															function (indexs) {
																taskStatus[index] = false;
																layer.close(indexs);
																cancelScanTaskRequest(id, function (rdata) {
																	if (!rdata.status) return bt_tools.msg(rdata);
																	renderInitView();
																});
															}
														);
													} else {
														renderInitView();
													}
												}
											});
										/**
										 * @description 渲染扫描初始化页面
										 */
										function renderInitView() {
											id = null;
											taskStatus[idx] = false;
											taskPath = '';
											taskList = {};
											$(layero).find('.disk_cont').removeClass('hide').siblings('.disk_scan_cont').addClass('hide');
											$(layero).find('.layui-layer-close1').show();
											$(layero).find('.disk-file-view,.disk-scan-view').addClass('hide');
											$(layero).find('.disk-file-load').css('display', 'none');
										}

										// 扫描
										$(layero)
											.find('.disk_scanning_btn')
											.unbind('click')
											.on('click', function () {
												// if(taskStatus.some(function (item){ return item === true })) {
												// if(bt.get_cookie('taskStatus') === 'true') {
												//   return layer.tips('有任务在执行，请稍后再操作！', $(this), {tips: [3, '#f00']});
												// }
												is_remove_disk[idx] = false;
												var $path = $(this).data('path');
												//判断是否安装插件
												bt.soft.get_soft_find('disk_analysis', function (dataRes) {
													if (dataRes.setup && dataRes.endtime > 0) {
														layer.closeAll();
														bt.set_cookie('diskPath', $path);
														bt.set_cookie('taskStatus', true);
														bt.soft.set_lib_config(dataRes.name, dataRes.title, dataRes.version);
													} else {
														var item = {
															name: 'disk_analysis',
															pluginName: 'Disk_analysis',
															ps: 'Quickly analyze disk/Hard disk usage',
															preview: false,
															limit: 'ltd',
															description: ['Check hard disk space', 'Occupancy percentage display'],
															imgSrc: 'https://www.bt.cn/Public/new/plugin/disk_analysis/1.png',
														};
														product_recommend.recommend_product_view(
															item,
															{
																imgArea: ['783px', '718px'],
															},
															'ltd',
															120,
															item.name
														);
														var is_buy = dataRes.endtime < 0 && dataRes.pid > 0;
														$('.buyNow')
															.text(is_buy ? 'Buy now' : 'Install now')
															.unbind('click')
															.click(function () {
																if (is_buy) {
																	bt.soft.product_pay_view({
																		name: dataRes.title,
																		pid: dataRes.pid,
																		type: dataRes.type,
																		plugin: true,
																		renew: -1,
																		ps: dataRes.ps,
																		ex1: dataRes.ex1,
																		totalNum: 120,
																	});
																} else {
																	bt.soft.install('disk_analysis');
																}
															});
													}
												});
												return;
												var ltd = bt.get_cookie('ltd_end');
												if (ltd < 0) {
													var item = {
														name: 'disk_analysis',
														pluginName: 'Disk_analysis',
														ps: 'Quickly analyze disk/Hard disk usage',
														preview: false,
														limit: 'ltd',
														description: ['Check hard disk space', 'Occupancy percentage display'],
														imgSrc: 'https://www.bt.cn/Public/new/plugin/disk_analysis/1.png',
													};
													product_recommend.recommend_product_view(
														item,
														{
															imgArea: ['783px', '718px'],
														},
														'ltd',
														120,
														item.name
													);
												} else {
													$.post('/files/size/scan_disk_info', { path: $path }, function (rdata) {
														if (!rdata.status) {
															if (rdata['code'] && rdata['code'] === 404) {
																bt.soft.install('disk_analysis');
															}
														} else {
															var $scanView = $(layero).find('.disk-scan-view');
															var shellView = $(layero).find('.disk-scan-view pre');
															$scanView.removeClass('hide');
															$(layero).find('.disk-file-view').addClass('hide');
															$(layero).find('.disk_cont').addClass('hide').siblings('.disk_scan_cont').removeClass('hide');
															taskStatus[$(layero).find('.disk_scanning').data('index')] = true;
															renderScanTitle(shellView, '开始扫描磁盘目录\n', true);
															renderScanTitle(shellView, '<span style="display:flex;" class="omit">目录正在扫描中<span>\n');
															renderTaskSpeed(
																function (rdata) {
																	id = rdata.id;
																	$(layero).find('.disk_scanning').data('id', id);
																},
																function () {
																	renderScanTitle(shellView, '扫描完成，等待扫描结果返回\n');
																	renderFilesView({
																		path: $path,
																		init: true,
																	});
																}
															);
														}
													});
												}
											});

										/**
										 * @description 渲染文件列表
										 * @param {Object} data 数据
										 */
										function renderFilesView(data, flag) {
											var param = {
												root_path: data.path,
											};
											if (data['subdir']) param.path = data.subdir;
											if (flag) $(layero).find('.disk-file-load').css('display', 'flex');
											bt_tools.send({ url: '/files/size/get_scan_log', data: param }, function (rdata) {
												if (flag) $(layero).find('.disk-file-load').css('display', 'none');
												var $fileView = $(layero).find('.disk-file-view');
												$fileView.removeClass('hide').prev().addClass('hide');
												var path = rdata.fullpath;
												path = path.replace(/(\\)+/g, '/');
												if (data.init) taskPath = path;
												if (!taskList.hasOwnProperty(path)) taskList[path] = rdata;
												renderFilesTable(rdata, path);
												renderFilesPath(path);
											});
										}
										// 渲染文件表格
										function renderFilesTable(rdata, path) {
											var $fileTableBody = $(layero).find('.filescan-list-body');
											var list = rdata.list;
											var html = '';
											for (var i = 0; i < list.length; i++) {
												var item = list[i];
												var isDir = item.type == 1;
												html +=
													'<div class="filescan-list-item" data-type="' +
													(isDir ? 'folder' : 'files') +
													'" data-subdir="' +
													rdata.fullpath +
													'/' +
													item.name +
													'" data-path="' +
													(path + '/' + item.name) +
													'">' +
													'<div class="filescan-list-col text-left nowrap" title="' +
													(path + '/' + item.name).replace('//', '/') +
													'">' +
													'<span class="file-type-icon file_' +
													(isDir ? 'folder' : 'icon') +
													'"></span>' +
													'<a class="path cut-path cursor" data-type="' +
													(isDir ? 'folder' : 'files') +
													'" data-path="' +
													(path + '/' + item.name) +
													'">' +
													item.name +
													'</a>' +
													'</div>' +
													'<div class="filescan-list-col text-left nowrap">' +
													bt.format_size(isDir ? item.total_asize : item.asize) +
													'</div>' +
													'<div class="filescan-list-col text-right">' +
													'<a href="javascript:;" data-filename="' +
													item.name +
													'" data-fullpath="' +
													rdata.fullpath +
													'" data-path="' +
													(path + '/' + item.name) +
													'" data-type="' +
													(isDir ? '文件夹' : '文件') +
													'" class="btlink remove-files">删除</a>' +
													'</div>' +
													'</div>';
											}
											$fileTableBody.html(html);
											// 删除文件
											$(layero)
												.find('.remove-files')
												.click(function (e) {
													var path = $(this).data('path'),
														type = $(this).data('type'),
														fullpath = $(this).data('fullpath'),
														filename = $(this).data('filename');
													delFileDir(
														{
															path: path,
															type: type,
															filename: filename,
														},
														function (rdata) {
															bt_tools.msg(rdata);
															var list = taskList[fullpath].list.filter(function (item) {
																return item.name !== filename.toString();
															});
															taskList[fullpath].list = list;
															renderFilesTable(taskList[fullpath], fullpath);
														}
													);
													e.stopPropagation();
												});
											// 打开目录
											$(layero)
												.find('.filescan-list-item')
												.click(function () {
													var root_path = $(layero).find('.disk_scanning_btn').data('path');
													var path = $(this).data('subdir'),
														type = $(this).data('type');
													if (type !== 'folder' && typeof type !== 'undefined') return false;
													if (!taskList.hasOwnProperty(path.replace('//', '/'))) {
														renderFilesView(
															{
																path: root_path,
																subdir: path,
															},
															true
														);
													} else {
														var rdata = taskList[path.replace('//', '/')];
														renderFilesTable(rdata, path); // 渲染文件表格
														renderFilesPath(path); // 渲染文件路径
													}
												});
										}
										// 渲染文件路径
										function renderFilesPath(path) {
											var html = '';
											var newPath = '';
											var pathArr = [];
											var isLevel = false;
											var isInit = true;
											var omission_li = [];
											pathArr = path.replace(taskPath.replace(/(\/\/)+/g, '/'), '').split('/');
											if (pathArr.length >= 1 && pathArr[0] !== '') pathArr.unshift('');
											if (pathArr.length > 1 && pathArr[1] !== '') {
												var upperPath = (getDirPath(path, false) + '/').replace(/(\/\/)+/g, '/');
												if (pathArr.length > 1) upperPath = upperPath.replace(/\/$/g, '');
												$(layero).find('.disk_back_btn').data('path', upperPath);
											}
											if (pathArr.length > 2) isInit = true;
											for (var i = 0; i < pathArr.length; i++) {
												var element = pathArr[i];
												newPath += '/' + element;
												if (element === '' && i > 0) continue;
												var isLast = pathArr.length - 1 === i;
												var isFirst = i === 0;
												var currentPath = isFirst ? taskPath : taskPath + newPath;
												var divider = !isLast ? '<span class="divider">></span>' : '';
												var menuPath = isFirst ? '当前目录(' + taskPath + ')' : element;
												currentPath = currentPath.replace(/\/\//g, '/');
												if (i > 1 && i < pathArr.length - 1 && pathArr.length > 3) {
													if (isInit) {
														html +=
															'<span class="omission">\
														<a class="btlink" title="部分目录已经省略">...</a>\
														<ul></ul>\
														</span><span class="divider">></span>';
													}
													omission_li.push({ menuPath: element, currentPath: currentPath });
													isInit = false;
												} else {
													html +=
														'<a class="filescan-nav-item nowrap ' +
														(isLevel && !isLast ? 'btlink cut-path' : '') +
														(isFirst ? ' present' : '') +
														'" data-path="' +
														currentPath +
														'" title="' +
														currentPath +
														'">' +
														menuPath +
														'</a>' +
														divider;
												}
											}
											$(layero).find('#fileScanPath').html(html);
											if (omission_li.length > 0) {
												var omission = $(layero).find('.omission');
												var ul = omission.find('ul');
												for (var i = 0; i < omission_li.length; i++) {
													var element = omission_li[i];
													ul.append(
														'<li><a class="filescan-nav-item cut-path" data-path="' +
														element.currentPath +
														'" title="' +
														element.currentPath +
														'"><i class="file_folder_icon"></i><span>' +
														element.menuPath +
														'</span></a></li>'
													);
												}
												$(layero)
													.find('.omission')
													.click(function (e) {
														if ($(this).hasClass('active')) {
															$(this).removeClass('active');
														} else {
															$(this).addClass('active');
														}
														$(document).click(function (ev) {
															$(layero).find('.omission').removeClass('active');
															ev.stopPropagation();
															ev.preventDefault();
														});
														e.stopPropagation();
														e.preventDefault();
													});
											}
											//打开目录按钮
											$(layero)
												.find('#fileScanPath .filescan-nav-item')
												.click(function () {
													var root_path = $(layero).find('.disk_scanning_btn').data('path');
													var path = $(this).data('path'),
														type = $(this).data('type');
													if (type !== 'folder' && typeof type != 'undefined') return layer.msg('文件暂不支持打开', { icon: 0 });
													if (!taskList.hasOwnProperty(path.replace('//', '/'))) {
														renderFilesView({
															path: root_path,
															subdir: path,
														});
													} else {
														var rdata = taskList[path.replace('//', '/')];
														renderFilesTable(rdata, path); // 渲染文件表格
														renderFilesPath(path); // 渲染文件路径
													}
												});
										}
										/**
										 * @description 获取目录地址
										 * @param {string} path 路径
										 * @param {number} param 参数
										 */
										function getDirPath(path, param) {
											path.replace(/\/$/, '');
											var pathArr = path.split('/');
											if (pathArr.length === 1) return path;
											if (param === -1) pathArr.push(status);
											if (typeof param === 'boolean') pathArr.pop();
											return pathArr.join('/').replace(/(\/)$/, '');
										}
										/**
										 * @description 渲染文件追加功能
										 * @param {Element} el 控制器
										 * @param {String} html 文本
										 * @param {Boolean} isCover 是否覆盖，默认不覆盖
										 */
										function renderScanTitle(el, html, isCover) {
											var $el = typeof el === 'string' ? $(layero).find(el) : el;
											if (isCover) {
												$el.html(html);
											} else {
												$el.append(html);
											}
										}
										/**
										 * @description 渲染扫描进度
										 * @param {Function} callack 回调函数
										 * @param {Function} end 结束回调函数
										 */
										function renderTaskSpeed(callack, end) {
											getScanTaskRequest(false, function (rdata) {
												if (rdata.length === 0 || !taskStatus[$(layero).find('.disk_scanning').data('index')]) {
													if (end && taskStatus[$(layero).find('.disk_scanning').data('index')]) end(rdata);
													taskStatus[$(layero).find('.disk_scanning').data('index')] = false;
													return;
												}
												for (var i = 0; i < rdata.length; i++) {
													var item = rdata[i];
													if (item.name.indexOf('扫描目录文件大小') > -1) {
														if (callack) callack(rdata[0]);
														break;
													}
												}
												// 扫描目录文件大小
												setTimeout(function () {
													renderTaskSpeed(callack, end);
												}, 1000);
											});
										}
										/**
										 * @description 获取扫描任务
										 * @param {boolean} load 是否显示加载中
										 * @param {function} callback 回调函数
										 */
										function getScanTaskRequest(load, callback) {
											var isLoad = typeof load === 'function';
											if (isLoad) callback = load;
											bt_tools.send(
												'task/get_task_lists',
												{
													status: -3,
												},
												function (rdata) {
													if (callback) callback(rdata);
												},
												{
													load: isLoad ? '获取扫描任务详情' : false,
												}
											);
										}

										/**
										 * @description 删除文件或目录
										 * @param {Object} data
										 */
										function delFileDir(data, callback) {
											if (bt.get_cookie('file_recycle_status') === 'true') {
												bt.simple_confirm(
													{
														title: '删除' + data.type + '【' + data.filename + '】',
														msg:
															'删除' +
															data.type +
															'后，' +
															data.type +
															'将迁移至文件回收站，<span class="color-org">请确认删除的文件是不需要的文件，误删文件可能会导致系统崩溃，</span>是否继续操作？</span>',
													},
													function () {
														delFileRequest(data, function (res) {
															if (callback) callback(res);
															layer.msg(res.msg, {
																icon: res.status ? 1 : 2,
															});
														});
													}
												);
											} else {
												bt.compute_confirm(
													{
														title: '删除' + data.type + '【' + data.filename + '】',
														msg:
															'风险操作，当前未开启文件回收站，删除' +
															data.type +
															'将彻底删除，无法恢复，<span class="color-org">请确认删除的文件是不需要的文件，误删文件可能会导致系统崩溃，</span>是否继续操作？',
													},
													function () {
														delFileRequest(data, function (res) {
															if (callback) callback(res);
															layer.msg(res.msg, {
																icon: res.status ? 1 : 2,
															});
														});
													}
												);
											}
										}
										/**
										 * @description 删除文件（文件和文件夹）
										 * @param {Object} data 文件目录参数
										 * @param {Function} callback 回调函数
										 * @return void
										 */
										function delFileRequest(data, callback) {
											var _req = data.type === '文件' ? 'DeleteFile' : 'DeleteDir';
											bt_tools.send(
												'files/' + _req,
												{
													path: data.path,
												},
												function (res) {
													if (callback) callback(res);
												},
												{
													load: '删除文件/目录',
												}
											);
										}
									},
									cancel: function (index, layero) {
										if (taskStatus[$(layero).find('.disk_scanning').data('index')]) {
											layer.confirm(
												'取消扫描，将会中断当前扫描目录进程，是否继续？',
												{
													title: '取消扫描',
													closeBtn: 2,
													icon: 3,
												},
												function (indexs) {
													taskStatus[$(layero).find('.disk_scanning').data('index')] = false;
													layer.close(indexs);
													layer.close(index);
													cancelScanTaskRequest($(layero).find('.disk_scanning').data('id'), function (rdata) {
														if (!rdata.status) return bt_tools.msg(rdata);
													});
												}
											);
											return false;
										}
									},
								});
							}
							/**
							 * @description 删除扫描任务
							 * @param {string} id 任务id
							 * @param {function} callback 回调函数
							 */
							function cancelScanTaskRequest(id, callback) {
								bt_tools.send(
									'task/remove_task',
									{
										id: id,
									},
									function (rdata) {
										if (callback) callback(rdata);
									},
									{
										load: '取消扫描任务',
									}
								);
							}
						},
						function () {
							diskInterval = setInterval(function () {
								if ($('.disk_scanning_tips' + idx).length) {
									var diskX = $('.disk_scanning_tips' + idx).offset().left,
										diskY = $('.disk_scanning_tips' + idx).offset().top,
										diskW = $('.disk_scanning_tips' + idx).width(),
										diskH = $('.disk_scanning_tips' + idx).height();
									var diskChartY = $('#diskChart' + idx).offset().top,
										diskChartX = $('#diskChart' + idx).offset().left,
										diskChartW = $('#diskChart' + idx).width(),
										diskChartH = $('#diskChart' + idx).height();
									var is_move_disk = mouseX >= diskChartX && mouseX <= diskChartX + diskChartW && mouseY >= diskChartY && mouseY <= diskChartY + diskChartH;
									var is_move = mouseX >= diskX && mouseX <= diskX + diskW && mouseY >= diskY && mouseY <= diskY + diskH;
									if (!is_move && !is_move_disk) {
										$('.disk_scanning_tips' + idx).remove();
									}
								} else {
									clearInterval(diskInterval);
								}
							}, 500);
						}
					);
				if ($('.disk_scanning_tips' + i).length) {
					var disk = $('#diskChart' + i).data('disk');
					var size3 = parseFloat(disk.size[3].substring(0, disk.size[3].lastIndexOf('%')));
					$('.disk_scanning_tips' + i + ' .disk-body-list .progressBar span')
						.text(disk.size[3])
						.css({
							left: (size3 < 12 ? size3 + 2 : size3 - 11) + '%;',
							color: size3 < 12 ? '#666;' : '#fff',
						});
					var progressCss = {
						width: disk.size[3],
					};
					if (size3 === 100) progressCss.borderRadius = '2px';
					$('.disk_scanning_tips' + i + ' .disk-body-list .progressBar .progress').css(progressCss);
					$('.disk_scanning_tips' + i + ' .disk-body-list .progressBar .progress')
						.removeClass('bg-red bg-org bg-green')
						.addClass(size3 >= 80 ? (size3 >= 90 ? 'bg-red' : 'bg-org') : 'bg-green');
					$('.disk_scanning_tips' + i + ' .disk-body-list.use_disk').html(
						parseFloat(disk.size[2]) +
						' ' +
						disk.size[2].replace(parseFloat(disk.size[2]), '') +
						'可用，' +
						parseFloat(disk.size[1]) +
						' ' +
						disk.size[1].replace(parseFloat(disk.size[1]), '') +
						'已用，共' +
						parseFloat(disk.size[0]) +
						' ' +
						disk.size[0].replace(parseFloat(disk.size[0]), '')
					);
					$('.disk_scanning_tips' + i + ' .disk-body-list.inodes0').html('Inode总数：' + disk.inodes[0]);
					$('.disk_scanning_tips' + i + ' .disk-body-list.inodes1').html('Inode已用：' + disk.inodes[1]);
					$('.disk_scanning_tips' + i + ' .disk-body-list.inodes2').html('Inode可用：' + disk.inodes[2]);
					$('.disk_scanning_tips' + i + ' .disk-body-list.inodes3').html('Inode使用率：' + disk.inodes[3]);
				}
			}

			_this.get_server_info(rdata);

			// 未安装环境时弹出
			if (rdata.installed === false) bt.index.rec_install();

			if (rdata.user_info.status) {
				var rdata_data = rdata.user_info.data;
				bt.set_cookie('bt_user_info', JSON.stringify(rdata.user_info));
				$('.bind-user').html(rdata_data.username);
			} else {
				$('.bind-weixin a').attr('href', 'javascript:;');
				$('.bind-weixin a').click(function () {
					bt.msg({ msg: '请先绑定宝塔账号!', icon: 2 });
				});
			}
		});
		setTimeout(function () {
			_this.interval.start();
		}, 40);
		setTimeout(function () {
			index.get_index_list();
		}, 50);
		setTimeout(function () {
			_this.net.init();
		}, 60);
		setTimeout(function () {
			_this.iostat.init();
		}, 60);

		setTimeout(function () {
			bt.system.check_update(function (rdata) {
				if (rdata.status !== false) {
					var res = rdata.msg;
					var ignore = res.ignore;
					var beta = res.beta;
					var is_beta = res.is_beta;
					if (ignore.indexOf(is_beta ? beta.version : res.version) == -1) index.check_update(true);
					$('#toUpdate a').html(lan.index.update + '<i style="display: inline-block; color: red; font-size: 40px;position: absolute;top: -35px; font-style: normal; right: -8px;">.</i>');
					$('#toUpdate a').css('position', 'relative');
				}
				// if (rdata.msg.is_beta === 1) {
				//     $('#btversion').prepend('<span style="margin-right:5px;">Beta</span>');
				//     $('#btversion').append('<a class="btlink" href="https://www.bt.cn/bbs/forum-39-1.html" target="_blank">  ['+lan.index.find_bug_reward+']</a>');
				// }
			}, false);
		}, 70);
	},
	get_server_info: function (info) {
		var memFree = info.memTotal - info.memRealUsed;
		if (memFree < 64) {
			$('#messageError').show();
			$('#messageError').append('<p><span class="glyphicon glyphicon-alert" style="color: #ff4040; margin-right: 10px;">' + lan.index.mem_warning + '</span> </p>');
		}

		if (info.isuser > 0) {
			$('#messageError').show();
			$('#messageError').append(
				'<p><span class="glyphicon glyphicon-alert" style="color: #ff4040; margin-right: 10px;"></span>' +
				lan.index.user_warning +
				'<span class="c7 mr5" title="' +
				lan.index.safe_problem_cant_ignore +
				'" style="cursor:no-drop"> [' +
				lan.index.cant_ignore +
				']</span><a class="btlink" href="javascript:setUserName();"> [' +
				lan.index.edit_now +
				']</a></p>'
			);
		}

		if (info.isport === true) {
			$('#messageError').show();
			$('#messageError').append(
				'<p><span class="glyphicon glyphicon-alert" style="color: #ff4040; margin-right: 10px;"></span>' +
				lan.index.panel_port_tips +
				'<span class="c7 mr5" title="' +
				lan.index.panel_port_tip1 +
				'" style="cursor:no-drop"> [' +
				lan.index.panel_port_tip2 +
				']</span><a class="btlink" href="/config"> [' +
				lan.index.panel_port_tip3 +
				']</a></p>'
			);
		}
		var _system = info.system;
		$('#info').html(_system);
		$('#running').html(info.time);
		if (_system.indexOf('Windows') != -1) {
			$('.ico-system').addClass('ico-windows');
		} else if (_system.indexOf('CentOS') != -1) {
			$('.ico-system').addClass('ico-centos');
		} else if (_system.indexOf('Ubuntu') != -1) {
			$('.ico-system').addClass('ico-ubuntu');
		} else if (_system.indexOf('Debian') != -1) {
			$('.ico-system').addClass('ico-debian');
		} else if (_system.indexOf('Fedora') != -1) {
			$('.ico-system').addClass('ico-fedora');
		} else {
			$('.ico-system').addClass('ico-linux');
		}
	},
	render_disk: function (data) {
		if (data.items.length > 0) {
			var _tab = $(data.table);
			for (var i = 0; i < data.items.length; i++) {
				var item = data.items[i];
				var html = '';
				html += '<li class="col-xs-6 col-sm-3 col-md-3 col-lg-2 mtb20 circle-box text-center diskbox">';
				html += '<h3 class="c9 f15">' + item.name + '</h3>';
				html += '<div class="cicle">';
				html += '<div class="bar bar-left"><div class="bar-left-an bar-an"></div></div>';
				html += '<div class="bar bar-right"><div  class="bar-right-an bar-an"></div></div>';
				html += '<div class="occupy"><span>0</span>%</div>';
				html += '</div>';
				html += '<h4 class="c9 f15">' + item.title + '</h4>';
				html += '</li>';
				var _li = $(html);
				if (item.masks) {
					var mask = '';
					for (var j = 0; j < item.masks.length; j++) mask += item.masks[j].title + ': ' + item.masks[j].value + '<br>';
					_li.data('mask', mask);
					_li.find('.cicle').hover(
						function () {
							var _this = $(this);
							layer.tips(_this.parent().data('mask'), _this, { time: 0, tips: [1, '#999'] });
						},
						function () {
							layer.closeAll('tips');
						}
					);
				}
				var color = '#20a53a';
				if (parseFloat(item.rate) >= 80) color = '#ff9900';
				var size = parseFloat(item.free.substr(0, item.free.length - 1));
				var unit = item.free.substr(item.free.length - 1, 1);
				switch (unit) {
					case 'G':
						if (size < 1) color = '#dd2f00';
						break;
					case 'T':
						if (size < 0.1) color = '#dd2f00';
						break;
					default:
						color = '#dd2f00';
						break;
				}

				index.set_val(_li, { usage: item.rate, color: color });
				_tab.append(_li);
			}
		}
	},
	set_val: function (_li, obj) {
		//obj.usage = parseInt(obj.usage)
		if (obj.usage > 50) {
			setTimeout(function () {
				_li.find('.bar-right-an').css({ transform: 'rotate(45deg)', transition: 'transform 750ms linear' });
			}, 10);
			setTimeout(function () {
				_li.find('.bar-left-an').css({ transform: 'rotate(' + (((obj.usage - 50) / 100) * 360 - 135) + 'deg)', transition: 'transform 750ms linear' });
			}, 760);
		} else {
			if (parseInt(_li.find('.occupy span').html()) > 50) {
				setTimeout(function () {
					_li.find('.bar-right-an').css({ transform: 'rotate(' + ((obj.usage / 100) * 360 - 135) + 'deg)', transition: 'transform 750ms linear' });
				}, 760);
				setTimeout(function () {
					_li.find('.bar-left-an').css({ transform: 'rotate(-135deg)', transition: 'transform 750ms linear' });
				}, 10);
			} else {
				setTimeout(function () {
					_li.find('.bar-right-an').css({ transform: 'rotate(' + ((obj.usage / 100) * 360 - 135) + 'deg)', transition: 'transform 750ms linear' });
				}, 10);
			}
		}
		if (obj.items) {
			var item = {};
			for (var i = 0; i < obj.items.length; i++) {
				if (obj.usage <= obj.items[i].val) {
					item = obj.items[i];
					continue;
				}
				break;
			}
			if (item.title) obj.title = item.title;
			if (item.color) obj.color = item.color;
		}
		if (obj.color) {
			_li.find('.cicle .bar-left-an').css('border-color', 'transparent transparent ' + obj.color + ' ' + obj.color);
			_li.find('.cicle .bar-right-an').css('border-color', obj.color + ' ' + obj.color + ' transparent transparent');
			_li.find('.occupy').css('color', obj.color);
		}
		if (obj.title) _li.find('h4').text(obj.title);
		_li.find('.occupy span').html(obj.usage);
	},

	/**
	 * @description 渲染系统信息
	 * @param callback 回调函数
	 *
	 */
	reander_system_info: function (callback) {
		var _this = this;
		bt.system.get_net(function (res) {
			_this.chart_result = res;
			// 动态添加磁盘，并赋值disk_view
			if (_this.chart_view.disk == undefined) {
				for (var i = 0; i < res.disk.length; i++) {
					var diskHtml =
						"<li class='rank col-xs-6 col-sm-3 col-md-3 col-lg-2 mtb20 circle-box text-center'><div id='diskName" +
						i +
						"'></div><div class='chart-li' id='diskChart" +
						i +
						"'></div><div id='disk" +
						i +
						"'></div></li>";
					$('#systemInfoList').append(diskHtml);
					_this.disk_view.push(echarts.init(document.querySelector('#diskChart' + i)));
				}
			}

			// 负载
			var loadCount = Math.round((res.load.one / res.load.max) * 100) > 100 ? 100 : Math.round((res.load.one / res.load.max) * 100);
			loadCount = loadCount < 0 ? 0 : loadCount;
			var loadInfo = _this.chart_color_active(loadCount);

			// cpu
			var cpuCount = res.cpu[0];
			var cpuInfo = _this.chart_color_active(cpuCount);

			// 内存
			var memCount = Math.round((res.mem.memRealUsed / res.mem.memTotal) * 1000) / 10; // 返回 memRealUsed 占 memTotal 的百分比
			var memInfo = _this.chart_color_active(memCount);
			bt.set_cookie('memSize', res.mem.memTotal);

			// 磁盘
			var diskList = res.disk;
			var diskJson = [];
			for (var i = 0; i < diskList.length; i++) {
				var ratio = diskList[i].size[3];
				ratio = parseFloat(ratio.substring(0, ratio.lastIndexOf('%')));
				var diskInfo = _this.chart_color_active(ratio);
				diskJson.push(diskInfo);
			}

			// chart_json存储最新数据
			_this.chart_json['load'] = loadInfo;
			_this.chart_json['cpu'] = cpuInfo;
			_this.chart_json['mem'] = memInfo;
			_this.chart_json['disk'] = diskJson;
			// 初始化 || 刷新
			if (_this.chart_view.disk == undefined) {
				_this.init_chart_view();
			} else {
				_this.set_chart_data();
			}
			$('.rank .titles').show();

			var net_key = bt.get_cookie('network_io_key');
			if (net_key) {
				res.up = res.network[net_key].up;
				res.down = res.network[net_key].down;
				res.downTotal = res.network[net_key].downTotal;
				res.upTotal = res.network[net_key].upTotal;
				res.downPackets = res.network[net_key].downPackets;
				res.upPackets = res.network[net_key].upPackets;
				res.downAll = res.network[net_key].downTotal;
				res.upAll = res.network[net_key].upTotal;
			}
			var net_option = '<option value="all">All</option>';
			$.each(res.network, function (k, v) {
				var act = k == net_key ? 'selected' : '';
				net_option += '<option value="' + k + '" ' + act + '>' + k + '</option>';
			});

			$('select[name="network-io"]').html(net_option);
			//刷新流量
			$('#upSpeed').html(res.up.toFixed(2) + ' KB');
			$('#downSpeed').html(res.down.toFixed(2) + ' KB');
			$('#downAll').html(bt.format_size(res.downTotal));
			$('#upAll').html(bt.format_size(res.upTotal));
			index.net.add(res.up, res.down);
			var disk_key = bt.get_cookie('disk_io_key') || 'ALL',
				disk_io_data = res.iostat[disk_key || 'ALL'],
				mb = 1048576,
				ioTime = disk_io_data.write_time > disk_io_data.read_time ? disk_io_data.write_time : disk_io_data.read_time;
			$('#readBytes').html(bt.format_size(disk_io_data.read_bytes));
			$('#writeBytes').html(bt.format_size(disk_io_data.write_bytes));
			$('#diskIops').html(disk_io_data.read_count + disk_io_data.write_count);
			$('#diskTime')
				.html(ioTime + ' ms')
				.css({ color: ioTime > 100 && ioTime < 1000 ? '#ff9900' : ioTime >= 1000 ? 'red' : '#20a53a' });

			index.iostat.add((disk_io_data.read_bytes / mb).toFixed(2), (disk_io_data.write_bytes / mb).toFixed(2), disk_io_data);

			var disk_option = '';
			$.each(res.iostat, function (k, v) {
				disk_option += '<option value="' + k + '" ' + (k == disk_key ? 'selected' : '') + '>' + (k == 'ALL' ? 'All' : k) + '</option>';
			});
			$('select[name="disk-io"]').html(disk_option);

			if (index.net.table)
				index.net.table.setOption({
					xAxis: { data: index.net.data.aData },
					series: [
						{ name: lan.index.net_up, data: index.net.data.uData },
						{ name: lan.index.net_down, data: index.net.data.dData },
					],
				});
			if (index.iostat.table)
				index.iostat.table.setOption({
					xAxis: { data: index.iostat.data.aData },
					series: [
						{ name: 'Read Bytes', data: index.iostat.data.uData },
						{ name: 'Write Bytes', data: index.iostat.data.dData },
					],
				});
			if (callback) callback(res);
		});
	},
	/**
	 * @description 渲染画布视图
	 */
	init_chart_view: function () {
		// 所有图表对象装进chart_view
		this.chart_view['load'] = echarts.init(document.querySelector('#loadChart'));
		this.chart_view['cpu'] = echarts.init(document.querySelector('#cpuChart'));
		this.chart_view['mem'] = echarts.init(document.querySelector('#memChart'));
		this.chart_view['disk'] = this.disk_view;

		// 图表配置项
		this.series_option = {
			series: [
				{
					type: 'gauge',
					startAngle: 90,
					endAngle: -270,
					animationDuration: 1500,
					animationDurationUpdate: 1000,
					radius: '99%',
					pointer: {
						show: false,
					},
					progress: {
						show: true,
						overlap: false,
						roundCap: true,
						clip: false,
						itemStyle: {
							borderWidth: 1,
							borderColor: '#20a53a',
						},
					},
					axisLine: {
						lineStyle: {
							width: 7,
							color: [
								[0, 'rgba(204,204,204,0.5)'],
								[1, 'rgba(204,204,204,0.5)'],
							],
						},
					},
					splitLine: {
						show: false,
						distance: 0,
						length: 10,
					},
					axisTick: {
						show: false,
					},
					axisLabel: {
						show: false,
						distance: 50,
					},
					data: [
						{
							value: 0,
							detail: {
								offsetCenter: ['0%', '0%'],
							},
							itemStyle: {
								color: '#20a53a',
								borderColor: '#20a53a',
							},
						},
					],
					detail: {
						width: 50,
						height: 15,
						lineHeight: 15,
						fontSize: 17,
						color: '#20a53a',
						formatter: '{value}%',
						fontWeight: 'normal',
					},
				},
			],
		};
		this.set_chart_data();
	},
	/**
	 * @description 赋值chart的数据
	 *
	 */
	set_chart_data: function () {
		this.chart_active('load');
		this.chart_active('cpu');
		if (!this.release) {
			this.chart_active('mem');
		}
		for (var i = 0; i < this.chart_view.disk.length; i++) {
			this.series_option.series[0].data[0].value = this.chart_json.disk[i].val;
			this.series_option.series[0].data[0].itemStyle.color = this.chart_json.disk[i].color;
			this.series_option.series[0].data[0].itemStyle.borderColor = this.chart_json.disk[i].color;
			this.series_option.series[0].progress.itemStyle.borderColor = this.chart_json.disk[i].color;
			this.series_option.series[0].detail.color = this.chart_json.disk[i].color;
			this.chart_view.disk[i].setOption(this.series_option, true);
			$('#disk' + i).text(this.chart_result.disk[i].size[1] + ' / ' + this.chart_result.disk[i].size[0]);
			$('#diskName' + i).text(this.chart_result.disk[i].path);
		}
	},
	/**
	 * @description 赋值chart的数据
	 *
	 */
	chart_active: function (name) {
		// 图表数据
		this.series_option.series[0].data[0].value = this.chart_json[name].val;
		this.series_option.series[0].data[0].itemStyle.color = this.chart_json[name].color;
		this.series_option.series[0].data[0].itemStyle.borderColor = this.chart_json[name].color;
		this.series_option.series[0].progress.itemStyle.borderColor = this.chart_json[name].color;
		this.series_option.series[0].detail.color = this.chart_json[name].color;

		this.chart_view[name].setOption(this.series_option, true);

		// 文字
		var val = '';
		switch (name) {
			case 'load':
				val = this.chart_json[name].title;
				break;
			case 'cpu':
				val = this.chart_result.cpu[1] + ' ' + lan.index.cpu_core;
				break;
			case 'mem':
				val = this.chart_result.mem.memRealUsed + ' / ' + this.chart_result.mem.memTotal + '(MB)';
				break;
		}

		$('#' + name).text(val);
	},
	/**
	 * @description 赋值chart的颜色
	 *
	 */
	chart_color_active: function (number) {
		var activeInfo = {};
		for (var i = 0; i < this.load_config.length; i++) {
			if (number >= this.load_config[i].val) {
				activeInfo = JSON.parse(JSON.stringify(this.load_config[i]));
				break;
			} else if (number <= 30) {
				activeInfo = JSON.parse(JSON.stringify(this.load_config[3]));
				break;
			}
		}
		activeInfo.val = number;
		return activeInfo;
	},

	get_index_list: function () {
		bt.soft.get_index_list(function (rdata) {
			var con = '';
			var icon = '';
			var rlen = rdata.length;
			var clickName = '';
			var setup_length = 0;
			var softboxsum = 12;
			var softboxcon = '';
			for (var i = 0; i < rlen; i++) {
				if (rdata[i].setup) {
					setup_length++;
					if (rdata[i].admin) {
						clickName = ' onclick="bt.soft.set_lib_config(\'' + rdata[i].name + "','" + rdata[i].title + '\')"';
					} else {
						clickName = 'onclick="soft.set_soft_config(\'' + rdata[i].name + '\')"';
					}
					var icon = rdata[i].name;
					if (bt.contains(rdata[i].name, 'php-')) {
						icon = 'php';
						rdata[i].version = '';
					}
					var status = '';
					if (rdata[i].status) {
						status = '<span style="color:#20a53a" class="glyphicon glyphicon-play"></span>';
					} else {
						status = '<span style="color:red" class="glyphicon glyphicon-pause"></span>';
					}
					con +=
						'<div class="col-sm-3 col-md-3 col-lg-3" data-id="' +
						rdata[i].name +
						'">\
							<span class="spanmove"></span>\
							<div ' +
						clickName +
						'>\
							<div class="image"><img width="48" src="/static/img/soft_ico/ico-' +
						icon +
						'.png"></div>\
							<div class="sname">' +
						rdata[i].title +
						' ' +
						rdata[i].version +
						status +
						'</div>\
							</div>\
						</div>';
				}
			}
			$('#indexsoft').html(con);
			// 推荐安装软件
			try {
				var recomConfig = product_recommend.get_recommend_type(1);
				if (recomConfig) {
					var pay_status = product_recommend.get_pay_status();
					for (var i = 0; i < recomConfig['list'].length; i++) {
						const item = recomConfig['list'][i];
						if (setup_length > softboxsum) break;
						if (pay_status.is_pay && item['install']) continue;
						softboxcon +=
							'<div class="col-sm-3 col-md-3 col-lg-3">\
                      <div class="recommend-soft recom-iconfont">\
                        <div class="product-close hide">关闭推荐</div>\
                        <div class="images"><img src="/static/img/soft_ico/ico-' +
							item['name'] +
							'.png"></div>\
                        <div class="product-name">' +
							item['title'] +
							'</div>\
                        <div class="product-pay-btn">\
                        ' +
							(item['isBuy'] && !item['install']
								? '<button class="btn btn-sm btn-success home_recommend_btn" style="margin-left:0;" onclick="bt.soft.install(\'' + item['name'] + '\')">Install</button>'
								: '<a class="btn btn-sm btn-default mr5 ' +
								(!item.preview ? 'hide' : '') +
								'" href="' +
								item.preview +
								'" target="_blank">Preview</a><button type="submit" class="btn btn-sm btn-success home_recommend_btn" onclick="product_recommend.pay_product_sign(\'pro\',' +
								item.pay +
								')">Buy now</button>') +
							'\
                        </div>\
                      </div>\
                    </div>';
						setup_length++;
					}
				}
			} catch (error) {
				console.log(error);
			}
			//软件位置移动
			if (setup_length <= softboxsum) {
				for (var i = 0; i < softboxsum - setup_length; i++) {
					softboxcon += '<div class="col-sm-3 col-md-3 col-lg-3 no-bg"></div>';
				}
				$('#indexsoft').append(softboxcon);
			}
			$('#indexsoft').dragsort({ dragSelector: '.spanmove', dragBetween: true, dragEnd: saveOrder, placeHolderTemplate: "<div class='col-sm-3 col-md-3 col-lg-3 dashed-border'></div>" });

			function saveOrder() {
				var data = $('#indexsoft > div')
					.map(function () {
						return $(this).attr('data-id');
					})
					.get();
				data = data.join('|');
				bt.soft.set_sort_index(data);
			}
		});
	},
	check_update: function () {
		if ($('.layui-layer-dialog').length > 0) return false;
		var loadT = bt.load();
		bt.system.check_update(function (rdata) {
			loadT.close();
			if (rdata.status === false && typeof rdata.msg === 'string') {
				try {
					messagebox();
				} catch (err) { }
				layer.msg(rdata.msg, { icon: 2 });
				return;
			}
			var data = rdata.msg;
			var is_beta = data.is_beta;
			var beta = data.beta;
			var versionData = is_beta ? beta : data;
			var isOld = rdata.status;

			if (isOld) {
				content =
					'\
					<div class="update-title">[Linux' +
					(rdata.msg.is_beta == 1 ? lan.index.test_version : lan.index.final_version) +
					'] - ' +
					lan.index.update_log +
					'</div>\
						<img class="update_bg" src="static/img/update_1.png" alt="" />\
						<div class="setchmod bt-form">\
							<div class="update_title">\
								<div class="sup_title">' +
					lan.index.have_new_version +
					'</div>\
								<div class="sub_title">' +
					lan.index.last_version +
					'<a href="https://www.aapanel.com/forum/d/9-aapanel-linux-panel-6-1-5-installation-tutorial/36" target="_blank" class="btlink" title="' +
					lan.index.check_version_log +
					'">' +
					lan.index.bt_linux +
					(is_beta === 1 ? lan.index.test_version : lan.index.final_version) +
					' ' +
					versionData.version +
					'</a>' +
					(!isOld ? '&nbsp;&nbsp;' + lan.index.update_date + versionData.uptime : '') +
					'</div>\
							</div>\
							<div class="update_conter">' +
					(isOld ? '<div class="update_logs">' + versionData.updateMsg + '</div><hr>' : '') +
					'<div class="update_tips">' +
					lan.index.last_version_is +
					(is_beta ? lan.index.final_version : lan.index.test_version) +
					(is_beta ? data.version : beta.version) +
					'&nbsp;&nbsp;&nbsp;' +
					lan.index.update_time +
					'&nbsp;' +
					(is_beta ? data.uptime : beta.uptime) +
					'&nbsp;&nbsp;&nbsp;\
								' +
					(!is_beta
						? '<span>' + lan.index.update_verison_click + '<a href="javascript:;" onclick="index.beta_msg()" class="btlink btn_update_testPanel">' + lan.index.check_detail + '</a></span>'
						: '<span>' + lan.index.change_final_click + '<a href="javascript:;" onclick="index.to_not_beta()" class="btlink btn_update_testPanel">' + lan.index.change_final + '</a></span>') +
					'\
							</div>\
						</div>\
						<div class="bt-form-btn ' +
					(!isOld ? 'hide' : '') +
					'">\
							<button type="button" class="btn ignore-renew">' +
					lan.index.ignore_update +
					'</button>\
							<button type="button" class="btn btn-success btn_update_panel" onclick="index.to_update()" >' +
					lan.index.update_go +
					'</button>\
						</div>\
					</div>';
			} else {
				content =
					'\
					<div class="update_back"><img src="/static/img/update_back.png"></div>\
						<div class="setchmod bt-form">\
							<div class="update_title">\
								<img src="/static/img/update-icon.png"/>\
								<span>' +
					lan.index.last_version_now +
					'</span>\
							</div>\
							<div class="update_version">\
								<span>' +
					lan.index.this_version +
					'<a href="https://www.aapanel.com/forum/d/9-aapanel-linux-panel-6-1-5-installation-tutorial/36" target="_blank" class="btlink" title="' +
					lan.index.check_this_version_log +
					'">' +
					lan.index.bt_linux +
					(rdata.msg.is_beta == 1 ? lan.index.test_version + ' ' + rdata.msg.beta.version : lan.index.final_version + ' ' + rdata.msg.version) +
					'</a></span><span style="margin-left:25px">' +
					lan.index.release_time +
					versionData.uptime +
					'</span>\
							</div>\
							<div class="update_conter">\
								<div class="update_tips">\
									<div class="tip_version">\
										<span class="mr10">' +
					lan.index.last_version_is +
					(is_beta ? lan.index.final_version : lan.index.test_version) +
					(is_beta ? data.version : data.beta.version) +
					'</span>\
										<span class="ml10">' +
					lan.index.update_time +
					(is_beta ? data.uptime.replaceAll('/', '-') : beta.uptime.replaceAll('/', '-')) +
					'</span>\
									</div>\
									' +
					(!is_beta
						? '<span style="margin-top:8px;">' +
						lan.index.update_verison_click +
						'<a href="javascript:;" onclick="index.beta_msg()" class="btlink btn_update_testPanel">' +
						lan.index.check_detail +
						'</a></span>'
						: '<span><a href="javascript:;" onclick="index.to_not_beta()" class="btlink btn_update_testPanel">' + lan.index.change_final + '</a></span>') +
					'\
									</span>\
								</div>\
							</div>\
						</div>\
						<style>\
							.update_title{display:flex;justify-content:center;align-items:center;position: relative;vertical-align: middle;margin: 12px 0;}\
							.update_title img{width:32px;margin-top: 4px;margin-right: 8px;}\
							.layui-layer-title{border:none;}\
							.update_title .layui-layer-ico{display: block;left: 40px !important;top: 1px !important;}\
							.update_back{background:linear-gradient(to top,rgb(255 255 255),#37BC51);position:absolute;width:100%;height:100px;z-index:-1;}\
							.update_back img{position:absolute;top:0;width:100%}\
							.update_title span{font-weight: 700;display: inline-block;color: #555;line-height: 32px;font-size: 24px;}\
							.update_conter{background: rgb(247, 252, 248);border-radius: 4px;padding: 24px 16px;margin:20px 32px 32px;margin-top: 16px;border: 1px solid #efefef;}\
							.update_version{font-size: 13px;text-align:center;font-weight:500;margin:0 36px 0;display:flex;justify-content:space-between;}\
							.update_version span{display:inline-block !important;text-align:left;}\
							.update_logs{font-size: 12px;color:#555;max-height:200px;overflow:auto;}\
							.update_tips{font-size: 12px;color:rgb(51, 51, 51);font-weight:400;}\
							.update_tips>span{font-size: 12px;color:rgb(51, 51, 51);font-weight:400;margin-top:0;}\
							.update_conter span{display: block;font-size:12px;color:#666}\
							.bt-form-btn {text-align: center;padding: 10px 0;}\
							.bt-form-btn .btn:nth-child(1):hover {background: #d4d4d4}\
							.bt-form-btn .btn {display: inline-block;line-height: 38px;height: 40px;border-radius: 20px;width: 140px;padding:0;margin-right: 30px;font-size:13.5px;}\
							.bt-form-btn .btn:nth-child(2) {margin-right: 0;}\
							.setchmod{height:auto;background-color:white;margin-top:32px;background:linear-gradient(to top,rgb(255 255 255),rgb(255 255 255),rgb(255 255 255),rgb(255 255 255),rgba(255,255,255,0));display:flex;justify-content:center;flex-direction:column;border-radius: 4px;}\
							.setchmod.bt-form .btswitch-btn {margin-bottom: 0;height: 1.9rem;width: 3.2rem;position: relative;top: 4.5px;}\
							.tip_version{width:100%;display:flex;flex-direction:row;}\
					</style>';
			}
			bt.open({
				type: 1,
				title: isOld
					? false
					: [
						'[Linux' + (rdata.msg.is_beta == 1 ? lan.index.test_version : lan.index.final_version) + '] - ' + lan.index.update_log,
						'background-color:#37BC51;color:white;height:36px;padding:0 80px 0 13.5px;',
					],
				area: isOld ? '480px' : '530px',
				shadeClose: false,
				skin: 'layui-layer-dialog' + (!isOld ? '' : ' new-layer-update active'),
				closeBtn: 2,
				content: content,
				success: function (layers, indexs) {
					if (!isOld) $(layers).find('.layui-layer-content').css('padding', '0');
					$('.ignore-renew').on('click', function () {
						bt.send('ignore_version', 'ajax/ignore_version', { version: versionData.version }, function (rdata) {
							bt.msg(rdata);
							if (rdata.status) layer.close(indexs);
						});
					});
				},
				cancel: function () {
					if (isOld) bt.send('ignore_version', 'ajax/ignore_version', { version: versionData.version });
				},
			});
		});
	},
	to_update: function () {
		layer.closeAll();
		bt.system.to_update(function (rdata) {
			if (rdata.status) {
				bt.msg({ msg: rdata.msg, icon: 1 });
				$('#btversion').html(rdata.version);
				$('#toUpdate').html('');
				bt.system.reload_panel();
				setTimeout(function () {
					window.location.reload();
				}, 3000);
			} else {
				bt.msg({ msg: rdata.msg, icon: 5, time: 5000 });
			}
		});
	},
	to_not_beta: function () {
		bt.show_confirm(lan.index.change_final, lan.index.change_test_to_final, function () {
			bt.send('apple_beta', 'ajax/to_not_beta', {}, function (rdata) {
				if (rdata.status === false) {
					bt.msg(rdata);
					return;
				}
				bt.system.check_update(function (rdata) {
					index.to_update();
				});
			});
		});
	},
	beta_msg: function () {
		var new_load = bt.load();
		bt.send('get_beta_logs', 'ajax/get_beta_logs', {}, function (data) {
			var my_list = '';
			new_load.close();
			if (data.status == false) {
				layer.msg(data.msg, { icon: 2 });
				return false;
			}
			for (var i = 0; i < data.list.length; i++) {
				my_list +=
					'<div class="item_list">\
                                            <span class="index_acive"></span>\
                                            <div class="index_date">' +
					bt.format_data(data.list[i].uptime).split(' ')[0] +
					'</div>\
                                            <div class="index_title">' +
					data.list[i].version +
					'</div>\
                                            <div class="index_conter">' +
					data.list[i].upmsg +
					'</div>\
                                        </div>';
			}
			layer.open({
				type: 1,
				title: lan.index.apply_linux_test_version,
				area: '650px',
				shadeClose: false,
				skin: 'layui-layer-dialog',
				closeBtn: 2,
				content:
					'<div class="bt-form pd20" style="padding-bottom:50px;padding-top:0">\
                            <div class="bt-form-conter">\
                                <span style="font-weight: 600;">' +
					lan.index.apply_most_know +
					'</span>\
                                <div class="form-body">' +
					data.beta_ps +
					'</div>\
                            </div>\
                            <div class="bt-form-conter">\
                                <span style="font-size:16px;">' +
					lan.index.linux_test_version_update_log +
					'</span>\
                                <div class="item_box"  style="height:180px;overflow: auto;">' +
					my_list +
					'</div>\
                            </div>\
                            <div class="bt-form-line"> <label for="notice" style="cursor: pointer;"><input id="notice" disabled="disabled" type="checkbox" style="vertical-align: text-top;margin-right:5px"></input><span style="font-weight:500">' +
					lan.index.already_read +
					lan.index.apply_most_know1 +
					'<i id="update_time"></i></span></label></div>\
                            <div class="bt-form-submit-btn">\
                                <button type="button" class="btn btn-danger btn-sm btn-title" onclick="layer.closeAll()">' +
					lan.public.cancel +
					'</button>\
                                <button type="button" class="btn btn-success btn-sm btn-title btn_update_panel_beta" disabled>' +
					lan.index.update_go +
					'</button>\
                            </div>\
                            <style>\
                                .bt-form-conter{padding: 20px 25px;line-height: 29px;background: #f7f7f7;border-radius: 5px;padding-bottom:30px;margin-bottom:20px;}\
                                .bt-form-conter span{margin-bottom: 10px;display: block;font-size: 19px;text-align: center;color: #333;}\
                                .form-body{color: #333;}\
                                #notice span{cursor: pointer;}\
                                #update_time{font-style:normal;color:red;}\
                                .item_list{margin-left:95px;border-left:5px solid #e1e1e1;position:relative;padding:5px 0 0 2px}.index_title{border-bottom:1px solid #ececec;margin-bottom:5px;font-size:15px;color:#20a53a;padding-left:15px;margin-top:7px;margin-left:5px}.index_conter{line-height:25px;font-size:12px;min-height:40px;padding-left:20px;color:#888}.index_date{position:absolute;left:-90px;top:13px;font-size:13px;color:#333}.index_acive{width:15px;height:15px;background-color:#20a53a;display:block;border-radius:50%;position:absolute;left:-10px;top:21px}.index_acive::after{position:relative;display:block;content:"";height:5px;width:5px;display:block;border-radius:50%;background-color:#fff;top:5px;left:5px}\
                            </style>\
                        </div>',
			});
			var countdown = 5;
			function settime(val) {
				if (countdown == 0) {
					val.removeAttr('disabled');
					$('#update_time').text('');
					return false;
				} else {
					$('#update_time').text(lan.index.second_left_of_click.replace('{1}', countdown));
					countdown--;
					setTimeout(function () {
						settime(val);
					}, 1000);
				}
			}
			settime($('#notice'));
			$('#notice').click(function () {
				console.log($(this).prop('checked'));
				if ($(this).prop('checked')) {
					$('.btn_update_panel_beta').removeAttr('disabled');
				} else {
					$('.btn_update_panel_beta').attr('disabled', 'disabled');
				}
			});
			$('.btn_update_panel_beta').click(function () {
				bt.show_confirm(lan.index.update_test_version, lan.index.check_test_version_detail, function () {
					var loading = bt.load();
					bt.send('apple_beta', 'ajax/apple_beta', {}, function (rdata) {
						if (rdata.status === false) {
							bt.msg(rdata);
							return;
						}
						bt.system.check_update(function (res) {
							loading.close();
							index.to_update();
						});
					});
				});
			});
		});
	},
	re_panel: function () {
		layer.confirm(lan.index.rep_panel_msg, { title: lan.index.rep_panel_title, closeBtn: 2, icon: 3 }, function () {
			bt.system.rep_panel(function (rdata) {
				if (rdata.status) {
					bt.msg({ msg: lan.index.rep_panel_ok, icon: 1 });
					return;
				}
				bt.msg(rdata);
			});
		});
	},
	re_server: function () {
		bt.open({
			type: 1,
			title: lan.index.restart_serverorpanel,
			area: '330px',
			closeBtn: 2,
			shadeClose: false,
			content:
				'<div class="rebt-con"><div class="rebt-li"><a data-id="server" href="javascript:;">' +
				lan.index.restart_server +
				'</a></div><div class="rebt-li"><a data-id="panel" href="javascript:;">' +
				lan.index.restart_panel +
				'</a></div></div>',
		});
		setTimeout(function () {
			$('.rebt-con a').click(function () {
				var type = $(this).attr('data-id');
				switch (type) {
					case 'panel':
						layer.confirm(lan.index.panel_reboot_msg, { title: lan.index.panel_reboot_title, closeBtn: 2, icon: 3 }, function () {
							var loading = bt.load();
							interval_stop = true;
							bt.system.reload_panel(function (rdata) {
								loading.close();
								bt.msg(rdata);
							});
							setTimeout(function () {
								window.location.reload();
							}, 3000);
						});
						break;
					case 'server':
						var rebootbox = bt.open({
							type: 1,
							title: lan.index.reboot_title,
							area: ['500px', '280px'],
							closeBtn: 2,
							shadeClose: false,
							content:
								"<div class='bt-form bt-window-restart'>\
									<div class='pd15'>\
									<p style='color:red; margin-bottom:10px; font-size:15px;'>" +
								lan.index.reboot_warning +
								"</p>\
									<div class='SafeRestart' style='line-height:26px'>\
										<p>" +
								lan.index.reboot_ps +
								'</p>\
										<p>' +
								lan.index.reboot_ps_1 +
								'</p>\
										<p>' +
								lan.index.reboot_ps_2 +
								'</p>\
										<p>' +
								lan.index.reboot_ps_3 +
								'</p>\
										<p>' +
								lan.index.reboot_ps_4 +
								"</p>\
									</div>\
									</div>\
									<div class='bt-form-submit-btn'>\
										<button type='button' class='btn btn-danger btn-sm btn-reboot'>" +
								lan.public.cancel +
								"</button>\
										<button type='button' class='btn btn-success btn-sm WSafeRestart' >" +
								lan.public.ok +
								'</button>\
									</div>\
								</div>',
						});
						setTimeout(function () {
							$('.btn-reboot').click(function () {
								rebootbox.close();
							});
							$('.WSafeRestart').click(function () {
								var body = '<div class="SafeRestartCode pd15" style="line-height:26px"></div>';
								$('.bt-window-restart').html(body);
								$('.SafeRestartCode').append('<p>' + lan.index.reboot_msg_1 + '</p>');
								bt.pub.set_server_status_by("name={{session['webserver']}}&type=stop", function (r1) {
									$('.SafeRestartCode p').addClass('c9');
									$('.SafeRestartCode').append('<p>' + lan.index.reboot_msg_2 + '...</p>');
									bt.pub.set_server_status_by('name=mysqld&type=stop', function (r2) {
										$('.SafeRestartCode p').addClass('c9');
										$('.SafeRestartCode').append('<p>' + lan.index.reboot_msg_3 + '...</p>');
										bt.system.root_reload(function (rdata) {
											$('.SafeRestartCode p').addClass('c9');
											$('.SafeRestartCode').append('<p>' + lan.index.reboot_msg_4 + '...</p>');
											var sEver = setInterval(function () {
												bt.system.get_total(function () {
													clearInterval(sEver);
													$('.SafeRestartCode p').addClass('c9');
													$('.SafeRestartCode').append('<p>' + lan.index.reboot_msg_5 + '...</p>');
													setTimeout(function () {
														layer.closeAll();
													}, 3000);
												});
											}, 3000);
										});
									});
								});
							});
						}, 100);
						break;
				}
			});
		}, 100);
	},
	open_log: function () {
		return;
		bt.open({
			type: 1,
			area: '640px',
			title: lan.index.update_log,
			closeBtn: 2,
			shift: 5,
			shadeClose: false,
			content: '<div class="DrawRecordCon"></div>',
		});
		$.get(
			'https://www.bt.cn/api/panel/updateLinuxEn',
			function (rdata) {
				var body = '';
				for (var i = 0; i < rdata.length; i++) {
					body +=
						'<div class="DrawRecord DrawRecordlist">\
							<div class="DrawRecordL">' +
						rdata[i].addtime +
						'<i></i></div>\
							<div class="DrawRecordR">\
								<h3>' +
						rdata[i].title +
						'</h3>\
								<p>' +
						rdata[i].body +
						'</p>\
							</div>\
						</div>';
				}
				$('.DrawRecordCon').html(body);
			},
			'jsonp'
		);
	},
	get_cloud_list: function () {
		$.post('/plugin?action=get_soft_list', { type: 8, p: 1, force: 1, cache: 1 }, function (rdata) {
			console.log(lan.index.get_soft_list_success);
		});
	},
	// 获取安全风险列表
	get_warning_list: function (active, callback) {
		var that = this,
			obj = {};
		if (active == true) obj = { force: 1 };
		bt_tools.send({ url: '/v2/warning?action=get_list', data: obj }, function (res) {
			if (res.status !== -1) {
				that.warning_list = res.message;
				that.warning_num = res.message.risk.length;
				$('.warning_num')
					.css('color', that.warning_num > 0 ? 'red' : '#20a53a')
					.html(that.warning_num);
				$('.warning_scan_ps').html(that.warning_num > 0 ? 'This scan check <i>' + that.warning_num + '</i> risks, Suggested repair!' : 'There is no risk item detected in this scan, please keep it!');
				if (callback) callback(res.message);
			}
		});
	},
	getScanSpeed: function (sele, msg, url) {
		var that = this;
		if (!$(sele).length) return;
		bt_tools.send({ url: url }, function (rdata) {
			var percentage = rdata.percentage;
			body =
				'<p>' +
				msg +
				'<img src="/static/img/ing.gif"></p>\
				<div class="bt-progress"><div class="bt-progress-bar" style="width:' +
				percentage +
				'%">\
				<span class="bt-progress-text" style="left: ' +
				(percentage < 21 ? 3 : percentage - 16) +
				'%;">' +
				percentage +
				'%</span></div></div>';
			$(sele).prev().hide();
			$(sele).css({ 'margin-left': '-37px', width: '380px' });
			$(sele).parents('.layui-layer').css({ 'margin-left': '-100px' });
			$(sele).html(body);
			setTimeout(function () {
				that.getScanSpeed(sele, msg, url);
			}, 200);
		});
	},
	/**
	 * @description 获取时间简化缩写
	 * @param {Numbre} dateTimeStamp 需要转换的时间戳
	 * @return {String} 简化后的时间格式
	 */
	get_simplify_time: function (dateTimeStamp) {
		if (dateTimeStamp === 0) return 'Just';
		if (dateTimeStamp.toString().length == 10) dateTimeStamp = dateTimeStamp * 1000;
		var minute = 1000 * 60,
			hour = minute * 60,
			day = hour * 24,
			halfamonth = day * 15,
			month = day * 30,
			now = new Date().getTime(),
			diffValue = now - dateTimeStamp;
		if (diffValue < 0) return 'Just';
		var monthC = diffValue / month,
			weekC = diffValue / (7 * day),
			dayC = diffValue / day,
			hourC = diffValue / hour,
			minC = diffValue / minute;
		if (monthC >= 1) {
			result = '' + parseInt(monthC) + ' month ago';
		} else if (weekC >= 1) {
			result = '' + parseInt(weekC) + ' weeks ago';
		} else if (dayC >= 1) {
			result = '' + parseInt(dayC) + ' days ago';
		} else if (hourC >= 1) {
			result = '' + parseInt(hourC) + ' hours ago';
		} else if (minC >= 1) {
			result = '' + parseInt(minC) + ' mins ago';
		} else {
			result = 'Just';
		}
		return result;
	},
	/**
	 * @description 渲染安全模块视图
	 * @return 无返回值
	 */
	reader_warning_view: function () {
		var that = this;
		if (!that.warning_num && that.warning_num !== 0) {
			layer.msg('正在获取安全风险项，请稍后 ...', { icon: 0 });
			return false;
		}
		function reader_warning_list(data) {
			var html = '',
				scan_time = '',
				arry = [
					['risk', 'Risk'],
					['security', 'Security'],
					['ignore', 'Ignore'],
				],
				level = [
					['Low risk', '#e8d544'],
					['Medium risk', '#E6A23C'],
					['High risk', 'red'],
				];
			bt.each(arry, function (index, item) {
				var data_item = data[item[0]],
					data_title = item[1];
				html +=
					'<li class="module_item ' +
					item[0] +
					'">' +
					'<div class="module_head">' +
					'<span class="module_title">' +
					data_title +
					'</span>' +
					'<span class="module_num">' +
					data_item.length +
					'</span>' +
					'<span class="module_cut_show">' +
					(item[index] == 'risk' && that.warning_num > 0
						? '<i>Collapse</i><span class="glyphicon glyphicon-menu-up" aria-hidden="false"></span>'
						: '<i>Details</i><span class="glyphicon glyphicon-menu-down" aria-hidden="false"></span>') +
					'</span>' +
					'</div>' +
					(function (index, item) {
						var htmls = '<ul class="module_details_list ' + (item[0] == 'risk' && that.warning_num > 0 ? 'active' : '') + '">';
						bt.each(data_item, function (indexs, items) {
							if (!items.cve_id) {
								scan_time = items.check_time;
								htmls +=
									'<li class="module_details_item">' +
									'<div class="module_details_head">' +
									'<span class="module_details_title"  title="' +
									items.ps +
									'">\
													' +
									items.ps +
									'</span>\
												<i class="module_details_tips">(&nbsp;Checked: ' +
									(that.get_simplify_time(items.check_time) || 'Just') +
									', Time: ' +
									(items.taking > 1 ? items.taking + 'Sec' : (items.taking * 1000).toFixed(2) + 'ms') +
									'&nbsp;, Level: ' +
									(function (level) {
										var level_html = '';
										switch (level) {
											case 3:
												level_html += '<span style="color:red">High</span>';
												break;
											case 2:
												level_html += '<span style="color:#E6A23C">Medium</span>';
												break;
											case 1:
												level_html += '<span style="color:#e8d544">Low</span>';
												break;
										}
										return level_html;
									})(items.level) +
									')</i>' +
									'<span class="operate_tools">' +
									(item[0] != 'security'
										? '<a href="javascript:;" class="btlink cut_details">Detail</a>&nbsp;&nbsp;|&nbsp;&nbsp;<a href="javascript:;" data-model="' +
										items.m_name +
										'" data-title="' +
										items.title +
										'" ' +
										(item[0] == 'ignore' ? 'class="btlink"' : '') +
										' data-type="' +
										item[0] +
										'">' +
										(item[0] != 'ignore' ? 'Ignore' : 'Remove') +
										'</a>&nbsp;&nbsp;|&nbsp;&nbsp;<a href="javascript:;" class="btlink" data-model="' +
										items.m_name +
										'" data-title="' +
										items.title +
										'">Check</a>'
										: '<a href="javascript:;" class="btlink cut_details">Detail</a>') +
									'</span>' +
									'</div>' +
									'<div class="module_details_body">' +
									'<div class="module_details_line">' +
									'<div class="module_details_block"><span class="line_title">Test type: </span><span class="line_content">' +
									items.title +
									'</span></div>' +
									'<div class="module_details_block"><span class="line_title">Risk level: </span><span class="line_content" style="color:' +
									level[items.level - 1][1] +
									'">' +
									level[items.level - 1][0] +
									'</span></div>' +
									'</div>' +
									'<div class="module_details_line"><span class="line_title">Risk detail: </span><span class="line_content">' +
									items.msg +
									'</span></div>' +
									'<div class="module_details_line"><span class="line_title">' +
									(item[0] != 'security' ? 'Solution: ' : 'Suggest: ') +
									'</span><span class="line_content">' +
									(function () {
										var htmlss = '';
										bt.each(items.tips, function (indexss, itemss) {
											htmlss += '<i>' + (indexss + 1) + '. ' + itemss + '</i></br>';
										});
										return htmlss;
									})() +
									'</span></div>' +
									'<div class="module_details_line"><span class="line_title">Tips: </span><span class="line_content">' +
									items.remind +
									'</span></div>' +
									(items.help != ''
										? '<div class="module_details_line"><span class="line_title">Help: </span><span class="line_content"><a href="' +
										items.help +
										'" target="_blank" class="btlink">' +
										items.help +
										'</span></div>'
										: '') +
									'</div>' +
									'</li>';
							} else {
								htmls +=
									'<li class="module_details_item">' +
									'<div class="module_details_head">' +
									'<span class="module_details_title" title="' +
									items.vuln_name +
									'">' +
									items.vuln_name +
									'</span>\
											<i class="module_details_tips">(&nbsp;Checked: ' +
									(that.get_simplify_time(items.check_time) || 'Just') +
									'&nbsp;, Level: ' +
									(function (level) {
										var level_html = '';
										switch (level) {
											case 3:
												level_html += '<span style="color:red">High</span>';
												break;
											case 2:
												level_html += '<span style="color:#E6A23C">Medium</span>';
												break;
											case 1:
												level_html += '<span style="color:#e8d544">Low</span>';
												break;
										}
										return level_html;
									})(items.level) +
									'）</i>' +
									'<span class="operate_tools">' +
									(item[0] != 'security'
										? '<a href="javascript:;" class="btlink cut_details">Detail</a>&nbsp;&nbsp;|&nbsp;&nbsp;<a href="javascript:;" data-title="' +
										items.vuln_name +
										'" data-id="' +
										items.cve_id +
										'" ' +
										(item[0] == 'ignore' ? 'class="btlink"' : '') +
										' data-type="' +
										'vuln' +
										'">' +
										(item[0] != 'ignore' ? 'Ignore' : 'Remove') +
										'</a>&nbsp;&nbsp;|&nbsp;&nbsp;<a href="javascript:;" class="btlink" data-type="' +
										'vuln' +
										'" data-id="' +
										items.cve_id +
										'">Check</a>'
										: '<a href="javascript:;" class="btlink cut_details">Detail</a>') +
									'</span>' +
									'</div>' +
									'<div class="module_details_body">' +
									'<div class="module_details_line">' +
									'<div class="module_details_block"><span class="line_title">Vulnerability Number: </span><span class="line_content">' +
									items.cve_id +
									'</span></div>' +
									'<div class="module_details_block"><span class="line_title">Risk level: </span><span class="line_content" style="color:' +
									level[items.level - 1][1] +
									'">' +
									level[items.level - 1][0] +
									'</span></div>' +
									'</div>' +
									'<div class="module_details_line"><span class="line_title">Software involved: </span><span class="line_content">' +
									(function () {
										var htmlss = '';
										bt.each(items.soft_name, function (indexss, itemss) {
											htmlss += '<i>' + indexss + '&nbsp;:&nbsp;' + itemss + '</i></br>';
										});
										return htmlss;
									})() +
									'</span></div>' +
									'<div class="module_details_line"><span class="line_title">' +
									(item[0] != 'security' ? 'Solution: ' : 'Suggest: ') +
									'</span><span class="line_content">' +
									items.vuln_solution +
									'</span></div>' +
									'</div>' +
									'</li>';
							}
						});

						htmls += '</ul>';
						return htmls;
					})(index, item) +
					'</li>';
			});
			$('.warning_scan_body').html(html);
			scan_time = Date.now() / 1000;
			// $('.warning_scan_time').html('Checked:&nbsp;' + bt.format_data(scan_time)+'<a class="btlink" href="/project/security/report/html" target="_Blank" style="margin-left: 6px;text-decoration: underline;">>>Obtain test report </a>' );
			$('.warning_scan_time').html('Checked:&nbsp;' + bt.format_data(scan_time));
		}
		var dialog_forbid_data;
		var danger_check_data = [];
		bt.open({
			type: '1',
			title: 'Security risk',
			area: ['850px', '700px'],
			skin: 'warning_scan_view',
			content:
				'<div class="warning_scan_view" style="height: 100%;">' +
				'<div class="warning_scan_head">' +
				'<span class="warning_scan_ps">' +
				(that.warning_num > 0 ? 'This scan check <i>' + that.warning_num + '</i> risks, Suggested repair!' : 'This scan check no risks, please keep it!') +
				'</span>' +
				'<span class="warning_scan_time"></span>' +
				'<button class="warning_auto_repair">Repair</button>' +
				'<button class="warning_again_scan" style="right:160px;">Retest</button>' +
				'</div>' +
				'<ol class="warning_scan_body" style="min-height: 528px;"></ol>' +
				'</div>',
			success: function () {
				//检测按钮
				$('.warning_again_scan').click(function () {
					var loadT = bt.load("<div class='myspeed'>Re detecting security risks, please wait...</div>");
					setTimeout(function () {
						that.getScanSpeed('.myspeed', 'Security risks are being redetected, please wait', '/warning?action=get_scan_bar');
					}, 50);
					that.get_warning_list(true, function () {
						layer.msg('Scan succeeded', { icon: 1 });
						reader_warning_list(that.warning_list);
						if (that.warning_list.risk.length == 0) {
							$('.warning_auto_repair').css('display', 'none');
							$('.warning_again_scan').css('right', '20px');
						} else {
							$('.warning_auto_repair').css('display', 'inline');
							$('.warning_again_scan').css('right', '160px');
						}
					});
				});
				bt_tools.send({ url: '/v2/warning?action=get_list', data: { open: 1 } }, function (warInfo) {
					that.warning_list = warInfo.message;
					// 显示数据
					if (that.warning_list.risk.length == 0) {
						$('.warning_auto_repair').css('display', 'none');
						$('.warning_again_scan').css('right', '20px');
					}
					//一键修复按钮
					$('.warning_auto_repair').click(function () {
						dialog_forbid_data = [];
						danger_check_data = [];
						$.each(that.warning_list.risk, function (index_c, item_c) {
							//可修复项
							if (!item_c.cve_id) {
								if ($.inArray(item_c.m_name, warInfo.is_autofix) != -1) {
									danger_check_data.push(item_c);
								} else {
									dialog_forbid_data.push(item_c);
								}
							} else {
								if ($.inArray(item_c.cve_id, warInfo.is_autofix) != -1) {
									item_c['title'] = 'System vulnerability';
									item_c['ps'] = item_c.vuln_name;
									danger_check_data.push(item_c);
								} else {
									item_c['ps'] = item_c.vuln_name;
									dialog_forbid_data.push(item_c);
								}
							}
						});

						var contentHtml =
							'<div class="dialog">\
										<div class="forbid">\
											<div class="forbid_title">\
												<div>\
													<span>There are <span style="font-weight:600">' +
							dialog_forbid_data.length +
							'</span> risks that cannot be repaired with one click</span>\
													<span class="btlink">\
														<a class="btlink" id="look_detail">Detail</a>\
														<div class="daily_details_mask bgw hide"></div>\
													</span>\
												</div>\
											</div>\
											<div class="forbid_content">\
												<p>\
												The above <span style="font-weight:600">' +
							dialog_forbid_data.length +
							'</span> items may lead to normal website access and abnormal service operation after one-click repair (please repair manually)\
												</p>\
											</div>\
										</div>\
										<div class="auto_content">\
											<div>\
												<span id="choose_auto_repair">Please select the risk items to be repaired (selected: <span id="danger_length" style="font-weight:600">' +
							0 +
							'</span>)</span>\
												<div id="auto_repair"></div>\
											</div>\
										</div>\
										<div class="confirm_button">\
											<span style="font-size:12px;color:#f39c12;margin-right:8px">If you have installed [System hardening], please turn them off before repairing</span>\
											<span id="is_ltd" style="font-size:12px;color:#f39c12;margin-right:8px">For Professional Version only, please <span class="btlink openLtd">Upgrade now</span></span>\
											<button id="confirm_button" class="button-link">Repair</button>\
										</div>\
									</div>';

						if (!dialog_forbid_data.length || !danger_check_data.length) height = true;
						var check_data;
						var height = false;
						layer.open({
							title: 'One-click repair confirm information',
							content: contentHtml,
							btn: false,
							closeBtn: 2,
							area: height ? ['640px', '380px'] : ['640px', '480px'],
							success: function (layero, index) {
								check_data = bt_tools.table({
									el: '#auto_repair',
									data: danger_check_data,
									load: true,
									height: '178px',
									column: [
										{
											type: 'checkbox',
											width: 20,
										},
										{
											fid: 'title',
											title: 'Test Type',
										},
										{
											fid: 'ps',
											title: 'Risk Item',
										},
										{
											fid: 'level',
											title: 'Risk Level',
											width: 100,
											template: function (row) {
												return row.level == 1 ? '<span style="color:#e8d544">High</span>' : row.level == 2 ? '<span style="color:#E6A23C">Medium</span>' : '<span style="color:red">Low</span>';
											},
										},
									],
								});
								// 判定表格选中长度
								$('#auto_repair tbody input,#auto_repair thead input').change(function () {
									$('#danger_length').text(check_data.checkbox_list.length);
									if (check_data.checkbox_list.length) {
										$('#confirm_button').attr('disabled', false);
										$('#confirm_button').css('background-color', '#20a53a');
									} else {
										$('#confirm_button').attr('disabled', true);
										$('#confirm_button').css('background-color', 'rgb(203, 203, 203)');
									}
								});
								// 不存在不可修复项时
								if (!dialog_forbid_data.length) {
									$('#choose_auto_repair').html('Please select the risk items to be repaired (selected: <span id="danger_length" style="font-weight:600">' + 0 + '</span>)</span>');
									$('.forbid').css('display', 'none');
									$('.dialog').find('hr').css('display', 'none');
								}
								if (!danger_check_data.length) {
									$('.dialog').find('hr').css('display', 'none');
									$('#choose_auto_repair').html('There are no currently repairable risk items!');
									$('#confirm_button').attr('disabled', true);
									$('#confirm_button').css('background-color', 'rgb(203, 203, 203)');
								}
								// 一键修复
								$('#confirm_button').click(function (e) {
									if (check_data.checkbox_list.length != 0) {
										var danger_selected_data = [];
										$.each(check_data.checkbox_list, function (index, item) {
											danger_selected_data.push(danger_check_data[item].m_name || danger_check_data[item].cve_id);
										});
										that.auto_repair(danger_selected_data, that.warning_list);
									} else {
										layer.msg('No risk items are currently selected!', { type: 1 });
										e.stopPropagation();
										e.preventDefault();
									}
								});
								// 查看详情列表
								var _details =
									'<div class="divtable daliy_details_table" style="width: 420px; border: 1px solid #ddd;"><table class="table table-hover" id="daliy_details_table" style="border: none;">',
									thead = '',
									_tr = '';
								$.each(dialog_forbid_data, function (index, item) {
									_tr +=
										'<tr><td style="width:34px;height:25px;text-align:center">' +
										(index + 1) +
										'</td><td><span class="overflow_hide" style="width:230px" title="' +
										item.m_name +
										'">' +
										item.ps +
										'</span></td></tr>';
								});
								thead = '<thead><tr><th colspan="2">The following ' + dialog_forbid_data.length + ' items cannot be repaired with one click</th></tr></thead>';
								_details += thead + '<tbody>' + _tr + '</tbody></table></div>';

								$('.daily_details_mask').html(_details);

								$('#look_detail').on('click', function (e) {
									$('.daily_details_mask').prev('a').css('color', '#23527c');
									if (e.target.localName == 'a') {
										if ($('.daily_details_mask').hasClass('hide')) {
											$('.daily_details_mask').removeClass('hide').css({ right: 20, top: 50 });
										} else {
											$('.daily_details_mask').addClass('hide');
											$('.daily_details_mask').prev('a').removeAttr('style');
										}
									}
									bt.fixed_table('daliy_details_table');
									$(document).click(function (ev) {
										$('.daily_details_mask').addClass('hide').prev('a').removeAttr('style');
										ev.stopPropagation();
									});
									e.stopPropagation();
								});

								$('i[data-checkbox=all]').click();

								// 是否为专业版
								var ltd = parseInt(bt.get_cookie('pro_end') || -1);
								if (ltd > 0) {
									$('#is_ltd').css('display', 'none');
								} else {
									$('#is_ltd').prev().hide();
									$('#confirm_button').attr('disabled', true);
									$('#confirm_button').css('background-color', 'rgb(203, 203, 203)');
								}

								$('.openLtd').click(function () {
									var item = {
										ps: 'Provide automatic repair solutions for security problems such as vulnerabilities and settings in the scanning server system, and perform automatic one-click repair for risk items scanned',
										description: ['Automatic Repair Scheme', 'Repair result display'],
										pluginName: 'Risk one-click repair',
										preview: false,
										imgSrc: 'https://www.bt.cn/Public/new/plugin/introduce/home/autoRepair.png',
									};
									bt.soft.product_pay_view({
										totalNum: 68,
										limit: 'pro',
										closePro: true,
										pluginName: item.pluginName,
										fun: function () {
											product_recommend.recommend_product_view(item, undefined, 'pro', 68, 'pro', true);
										},
									});
								});
							},
						});
					});
					// 3个大的下来的点击事件
					$('.warning_scan_body').on('click', '.module_item .module_head', function () {
						var _parent = $(this).parent(),
							_parent_index = _parent.index(),
							_list = $(this).next();
						if (parseInt($(this).find('.module_num').text()) > 0) {
							if (_list.hasClass('active')) {
								_list.css('height', 0);
								$(this).find('.module_cut_show i').text('Detail').next().removeClass('glyphicon-menu-up').addClass('glyphicon-menu-down');
								setTimeout(function () {
									_list.removeClass('active').removeAttr('style');
								}, 500);
							} else {
								$(this).find('.module_cut_show i').text('Collapse').next().removeClass('glyphicon-menu-down').addClass('glyphicon-menu-up');
								_list.addClass('active');
								var details_list = _list.parent().siblings().find('.module_details_list');
								details_list.removeClass('active');
								details_list.prev().find('.module_cut_show i').text('Detail').next().removeClass('glyphicon-menu-up').addClass('glyphicon-menu-down');
							}
						}
					});
					$('.warning_repair_scan').click(function () {
						bt.onlineService();
					});
					// 右边的操作
					$('.warning_scan_body').on('click', '.operate_tools a', function () {
						var index = $(this).index(),
							data = $(this).data();
						switch (index) {
							case 0:
								if ($(this).hasClass('active')) {
									$(this).parents('.module_details_head').next().hide();
									$(this).removeClass('active').text('Detail');
								} else {
									var item = $(this).parents('.module_details_item'),
										indexs = item.index();
									$(this).addClass('active').text('Collapse');
									item.siblings().find('.module_details_body').hide();
									item.siblings().find('.operate_tools a:eq(0)').removeClass('active').text('Detail');
									$(this).parents('.module_details_head').next().show();
									$('.module_details_list').scrollTop(indexs * 41);
								}

								break;
							case 1:
								if (data.type != 'ignore') {
									bt.confirm({ title: 'Ignore risk', msg: 'Confirm to ignore [' + data.title + '] risk?' }, function () {
										if (data.type != 'vuln') {
											that.warning_set_ignore(data.model, function (res) {
												that.get_warning_list(false, function () {
													if (!that.warning_list.risk.length) {
														$('.warning_auto_repair').css('display', 'none');
														$('.warning_again_scan').css('right', '40px');
													}
													reader_warning_list(that.warning_list);
												});
											});
										} else {
											// console.log('漏洞的');
											that.bug_set_ignore(data.id, function (res) {
												that.get_warning_list(false, function () {
													if (!that.warning_list.risk.length) {
														$('.warning_auto_repair').css('display', 'none');
														$('.warning_again_scan').css('right', '40px');
													}
													reader_warning_list(that.warning_list);
												});
											});
										}
									});
								} else {
									that.warning_set_ignore(data.model, function (res) {
										that.get_warning_list(false, function () {
											reader_warning_list(that.warning_list);
											if (that.warning_list.risk.length) {
												$('.warning_auto_repair').css('display', 'inline');
												$('.warning_again_scan').css('right', '160px');
											}
											setTimeout(function () {
												$('.module_item.ignore').click();
											}, 100);
										});
									});
								}
								break;
							case 2:
								if (data.type != 'vuln') {
									that.waring_check_find(data.model, function (res) {
										that.get_warning_list(false, function () {
											reader_warning_list(that.warning_list);
										});
									});
								} else {
									that.bug_check_find(data.id, function (res) {
										that.get_warning_list(false, function () {
											reader_warning_list(that.warning_list);
										});
									});
								}
								break;
						}
					});
					reader_warning_list(that.warning_list);
				});
			},
		});
		// var that = this;
		// function reader_warning_list(data){
		//     var html = '',scan_time = '',arry =  [['risk','Risk'],['security','Security'],['ignore','Ignore']],level = [['Low risk','#e8d544'],['Medium risk','#E6A23C'],['High risk','red']]
		//     bt.each(arry,function(index,item){
		//         var data_item = data[item[0]],data_title = item[1];
		//         html += '<li class="module_item '+ item[0] +'">'+
		//                 '<div class="module_head">'+
		//                     '<span class="module_title">'+ data_title +'</span>'+
		//                     '<span class="module_num">'+ data_item.length +'</span>'+
		//                     '<span class="module_cut_show">'+ (item[index] == 'risk' && that.warning_num > 0?'<i>Collapse</i><span class="glyphicon glyphicon-menu-up" aria-hidden="false"></span>':'<i>Details</i><span class="glyphicon glyphicon-menu-down" aria-hidden="false"></span>') +'</span>'+
		//                 '</div>'+
		//                 (function(index,item){
		//                     var htmls = '<ul class="module_details_list '+ (item[0] == 'risk' && that.warning_num > 0?'active':'') +'">';
		//                     bt.each(data_item,function(indexs,items){
		//                         scan_time = items.check_time;
		//                         htmls += '<li class="module_details_item">'+
		//                             '<div class="module_details_head">'+
		//                                 '<span class="module_details_title">'+ items.ps +'<i>（Checked: '+ (that.get_simplify_time(items.check_time) || 'Just') +', time: '+ ( items.taking>1?( items.taking +'Sec'):((items.taking * 1000).toFixed(2) +'ms')) +'）</i></span>'+
		//                                 '<span class="operate_tools">'+ (item[0] != 'security'?('<a href="javascript:;" class="btlink cut_details">Detail</a>&nbsp;&nbsp;|&nbsp;&nbsp;<a href="javascript:;" data-model="'+ items.m_name +'" data-title="'+ items.title +'" '+ (item[0]=='ignore'?'class=\"btlink\"':'') +' data-type="'+item[0]+'">'+ (item[0] != 'ignore'?'Ignore':'Remove') +'</a>&nbsp;&nbsp;|&nbsp;&nbsp;<a href="javascript:;" class="btlink" data-model="'+ items.m_name +'" data-title="'+ items.title +'">Check</a>'):'<a href="javascript:;" class="btlink cut_details">Detail</a>') +'</span>' +
		//                             '</div>'+
		//                             '<div class="module_details_body">'+
		//                                 '<div class="module_details_line">'+
		//                                     '<div class="module_details_block"><span class="line_title">Test type: </span><span class="line_content">'+ items.title +'</span></div>'+
		//                                     '<div class="module_details_block"><span class="line_title">Risk level: </span><span class="line_content" style="color:'+ level[items.level-1][1] +'">'+ level[items.level-1][0] +'</span></div>'+
		//                                 '</div>'+
		//                                 '<div class="module_details_line"><span class="line_title">Risk detail: </span><span class="line_content">'+ items.msg +'</span></div>'+
		//                                 '<div class="module_details_line"><span class="line_title">'+ (item[0] != 'security'?'Solution: ':'Suggest: ') +'</span><span class="line_content">'+
		//                                 (function(){
		//                                     var htmlss = '';
		//                                     bt.each(items.tips,function(indexss,itemss){
		//                                         htmlss +='<i>'+ (indexss+1) +'、'+ itemss  +'</i></br>';
		//                                     });
		//                                     return htmlss;
		//                                 }()) +'</span></div>'+
		//                                 (items.help != ''?('<div class="module_details_line"><span class="line_title">Help: </span><span class="line_content"><a href="'+ items.help +'" target="_blank" class="btlink">'+items.help +'</span></div>'):'') +
		//                             '</div>'+
		//                         '</li>';
		//                     });
		//                     htmls += '</ul>';
		//                     return htmls;
		//                 }(index,item))
		//             +'</li>'
		//     });
		//     $('.warning_scan_body').html(html);
		//     $('.warning_scan_time').html('Checked: &nbsp;'+ bt.format_data(scan_time));
		// }
		// bt.open({
		//     type:'1',
		//     title:'Security risk',
		//     area:['850px','700px'],
		//     skin:'warning_scan_view',
		//     content:'<div class="warning_scan_view">'+
		//         '<div class="warning_scan_head">'+
		//             '<span class="warning_scan_ps">'+ (that.warning_num>0?('This scan check <i>'+ that.warning_num +'</i> risks, Suggested repair!'):'This scan check no risks, please keep it!') +'</span>'+
		//             '<span class="warning_scan_time"></span>'+
		//             '<button class="warning_again_scan">Retest</button>'+
		//         '</div>'+
		//         '<ol class="warning_scan_body"></ol>'+
		//     '</div>',
		//     success:function(){
		//         $('.warning_again_scan').click(function(){
		//             var loadT = layer.msg('Re detecting security risks, please wait...',{icon:16});
		//             that.get_warning_list(true,function(){
		//                 layer.msg('Scan succeeded',{icon:1});
		//                 reader_warning_list(that.warning_list);
		//             });
		//         });
		//         $('.warning_scan_body').on('click','.module_item .module_head',function(){
		//             var _parent = $(this).parent(),_parent_index = _parent.index(),_list = $(this).next();
		//             if(parseInt($(this).find('.module_num').text()) > 0){
		//                 if(_list.hasClass('active')){
		//                     _list.css('height',0);
		//                     $(this).find('.module_cut_show i').text('Detail').next().removeClass('glyphicon-menu-up').addClass('glyphicon-menu-down');
		//                     setTimeout(function(){
		//                         _list.removeClass('active').removeAttr('style');
		//                     },500);
		//                 }else{
		//                     $(this).find('.module_cut_show i').text('Collapse').next().removeClass('glyphicon-menu-down').addClass('glyphicon-menu-up');
		//                     _list.addClass('active');
		//                     var details_list = _list.parent().siblings().find('.module_details_list');
		//                     details_list.removeClass('active');
		//                     details_list.prev().find('.module_cut_show i').text('Detail').next().removeClass('glyphicon-menu-up').addClass('glyphicon-menu-down')
		//                 }
		//             }
		//         });
		//         $('.warning_scan_body').on('click','.operate_tools a',function(){
		//             var index = $(this).index(),data = $(this).data();
		//             switch(index){
		//                 case 0:
		//                     if($(this).hasClass('active')){
		//                         $(this).parents('.module_details_head').next().hide();
		//                         $(this).removeClass('active').text('Detail');
		//                     }else{
		//                         var item = $(this).parents('.module_details_item'),indexs = item.index();
		//                         $(this).addClass('active').text('Collapse');
		//                         item.siblings().find('.module_details_body').hide();
		//                         item.siblings().find('.operate_tools a:eq(0)').removeClass('active').text('Detail');
		//                         $(this).parents('.module_details_head').next().show();
		//                         $('.module_details_list').scrollTop(indexs * 41);
		//                     }
		//                 break;
		//                 case 1:
		//                     if(data.type != 'ignore'){
		//                         bt.confirm({title:'Ignore risk',msg:'Confirm to ignore [ '+ data.title +' ] risk?'},function(){
		//                             that.warning_set_ignore(data.model,function(res){
		//                                 that.get_warning_list(false,function(){
		//                                     bt.msg(res)
		//                                     reader_warning_list(that.warning_list);
		//                                 });
		//                             });
		//                         });
		//                     }else{
		//                         that.warning_set_ignore(data.model,function(res){
		//                             that.get_warning_list(false,function(){
		//                                 bt.msg(res)
		//                                 reader_warning_list(that.warning_list);
		//                                 setTimeout(function(){
		//                                     $('.module_item.ignore').click();
		//                                 },100)
		//                             });
		//                         });
		//                     }
		//                 break;
		//                 case 2:
		//                     that.waring_check_find(data.model,function(res){
		//                         that.get_warning_list(false,function(){
		//                             bt.msg(res)
		//                             reader_warning_list(that.warning_list);
		//                         });
		//                     });
		//                 break;
		//             }
		//         });
		//         reader_warning_list(that.warning_list);
		//     }
		// })
	},
	/**
	 * @description 安全风险指定模块检查
	 * @param {String} model_name 模块名称
	 * @param {Function} callback 成功后的回调
	 * @return 无返回值
	 */
	waring_check_find: function (model_name, callback) {
		var loadT = layer.msg('Detecting the specified module, please wait...', { icon: 16, time: 0 });
		bt_tools.send({ url: '/v2/warning?action=check_find', data: { m_name: model_name } }, function (res) {
			bt.msg({ status: res.status === 0, msg: res.message.result });
			if (res.status !== false) {
				if (callback) callback(res);
			}
		});
	},

	/**
	 * @description:  安全风险一键修复
	 * @param {*} params 选中的修复项的数组
	 * @param {*} data 原先的数组
	 * @return {*}
	 */
	auto_repair: function (params, data) {
		var that = this;
		var res_data = [];
		var loadT = bt.load('<div class="repair_speed">Fixing the security risk, please wait...</div>');
		setTimeout(function () {
			that.getScanSpeed('.repair_speed', 'Fixing security risks', '/safe/security/get_repair_bar');
		}, 50);
		$.post('/safe/security/set_security', { data: JSON.stringify({ m_name: params }) }, function (rdata) {
			if (rdata.msg == 'The current features are exclusive to the professional edition') {
				layer.msg(rdata.msg);
				return;
			}
			var res_item = {};
			res_data = [];
			$.each(rdata.success, function (index, item) {
				res_item.status = item.result.status;
				res_item.type = item.result.type;
				res_item.msg = item.result.msg;
				res_item.m_name = item.m_name;
				res_data.push(res_item);
				res_item = {};
			});
			$.each(rdata.failed, function (index, item) {
				res_item.status = item.result.status;
				res_item.type = item.result.type;
				res_item.msg = item.result.msg;
				res_item.m_name = item.m_name;
				res_data.push(res_item);
				res_item = {};
			});
			if (rdata.cannot_automatically.length) {
				$.each(rdata.cannot_automatically, function (index, item) {
					res_item.m_name = item;
					res_item.status = 'ignore';
					res_data.push(res_item);
					res_item = {};
				});
			}
			var result_table =
				'<div><p style="margin-bottom:20px;font-size:16px">Repair result: Success <span style="color:#20a53a">' +
				rdata.success.length +
				'</span> items, Fail <span style="color:red">' +
				rdata.failed.length +
				'</span> items, Ignore <span style="color:#b9b9b9">' +
				rdata.cannot_automatically.length +
				'</span> items</p><div id="auto_repair_result"></div></div>' +
				'<div class="forbid_content"><p style="margin-bottom:20px;font-size:12px">After closing, risk items will be automatically re-detected. If you do not re-detect, please manually click the "Retest" button</br>If any item fails to be repaired, close the current window and repair the item manually based on the solution</div>';
			layer.open({
				title: 'Result',
				content: result_table,
				closeBtn: 2,
				area: '540px',
				btn: false,
				success: function (layero, index) {
					$('#auto_repair_result').empty();
					bt_tools.table({
						el: '#auto_repair_result',
						data: res_data,
						load: true,
						height: '240px',
						column: [
							{
								type: 'text',
								title: 'Risk item',
								template: function (row) {
									var rowData;
									$.each(data.risk, function (index_d, item_d) {
										if (!item_d.cve_id) {
											if (item_d.m_name == row.m_name) {
												rowData = '<span>' + item_d.title + '</span>';
											}
										} else {
											rowData = '<span>' + row.m_name + '</span>';
										}
									});
									return rowData;
								},
							},
							{
								type: 'text',
								title: 'Info (website or other)',
								width: 200,
								template: function (row) {
									if (row.type.length) {
										if (Array.isArray(row.type)) {
											var data = row.type.join(',');
											return '<span  class="result_span">' + data + '</span>';
										}
										return '<span class="result_span">' + row.type + '</span>';
									} else {
										return '<span>--</span>';
									}
								},
							},
							{
								title: 'Opt',
								type: 'text',
								align: 'right',
								template: function (row) {
									if (row.status == false) {
										return '<span style="color:red">Fail</span>';
									} else if (row.status == true) {
										return '<span style="color:#20a53a">Success</span>';
									} else if (row.status == 'ignore') {
										return '<span style="color:rgb(102, 102, 102)">Ignore risk</span>';
									}
								},
							},
						],
					});
				},
				cancel: function (index, layers) {
					res_data = [];
					layer.close(index);
					var loadT = layer.msg('Retesting for security risks, please wait...', {
						icon: 16,
					});
					$('.warning_again_scan').click();
				},
			});
		});
	},
	/**
	 * @description 安全风险指定模块是否忽略
	 * @param {String} model_name 模块名称
	 * @param {Function} callback 成功后的回调
	 * @return 无返回值
	 */
	warning_set_ignore: function (model_name, callback) {
		var loadT = layer.msg('Setting the specified module, please wait...', { icon: 16, time: 0 });
		bt_tools.send({ url: '/v2/warning?action=set_ignore', data: { m_name: model_name } }, function (res) {
			bt.msg({ status: res.status === 0, msg: res.message.result });
			if (res.status !== -1) {
				if (callback) callback(res);
			}
		});
	},
	/**
	 * @description 获取当前的产品状态
	 */
	get_product_status: function (callback) {
		// var loadT = layer.msg('正在获取产品状态，请稍候...', { icon: 16, time: 0 })
		bt.send('get_pd', 'ajax/get_pd', {}, function (res) {
			$('.btpro-gray').replaceWith($(res[0]));
			bt.set_cookie('pro_end', res[1]);
			bt.set_cookie('ltd_end', res[2]);
			if (res[1] === 0) {
				$('.btpro span').click(function (e) {
					layer.confirm('切换回免费版可通过解绑账号实现', { icon: 3, btn: ['解绑账号'], closeBtn: 2, title: '是否取消授权' }, function () {
						$.post('/ssl?action=DelToken', {}, function (rdata) {
							layer.msg(rdata.msg);
							setTimeout(function () {
								window.location.reload();
							}, 2000);
						});
					});
					e.stopPropagation();
				});
			}
			if (callback) callback();
		});
	},
	/**
	 * @description 推荐进阶版产品
	 */
	recommend_paid_version: function () {
		try {
			var recomConfig = product_recommend.get_recommend_type(0);
			var pay_status = product_recommend.get_pay_status();
			var is_pay = pay_status.is_pay;
			var advanced = pay_status.advanced;
			var end_time = pay_status.end_time;
			var html = '',
				list_html = '';
			if (!is_pay) advanced = ''; //未购买的时候，使用推荐内容
			if (recomConfig) {
				var item = recomConfig;
				for (let j = 0; j < item['ps'].length; j++) {
					const element = item['ps'][j];
					list_html += '<div class="item">' + element + '</div>';
				}
				var pay_html = '';
				if (is_pay) {
					pay_html =
						'<div class="product-buy ' +
						(advanced || item.name) +
						'-type">Expired: <span>' +
						(end_time === 0
							? 'Lifetime'
							: (end_time === -2 ? 'Expired' : bt.format_data(end_time, 'yyyy-MM-dd')) +
							'&nbsp;&nbsp;<a class="btlink" href="javascript:;" onclick="product_recommend.pay_product_sign(\'' +
							advanced +
							"'," +
							item.pay +
							')">Renew</a>') +
						'</span></div>';
				} else {
					pay_html =
						'<div class="product-buy"><button type="button" class="btn btn-xs btn-success" onclick="product_recommend.pay_product_sign(\'' +
						(advanced || item.name) +
						"'," +
						item.pay +
						')">Buy now</button></div>';
				}
				html =
					'<div class="conter-box bgw">\
          <div class="recommend-top pd15 ' +
					(is_pay ? advanced + '-bg' : '') +
					'">' +
					(!is_pay ? pay_html : '') +
					'<div class="product-ico ' +
					(advanced || item.name) +
					'' +
					(!is_pay ? '-pay' : '') +
					'-ico"></div>' +
					(is_pay ? pay_html : '') +
					'\
            <div class="product-label">' +
					list_html +
					'</div>\
          </div>\
        </div>';
				$('#home-recommend').html(html);
			}
		} catch (error) {
			console.log(error);
		}
	},
	disk_scan: function ($path) {
		bt.soft.get_soft_find('disk_analysis', function (dataRes) {
			if (dataRes.setup && dataRes.endtime > 0) {
				layer.closeAll();
				bt.set_cookie('diskPath', $path);
				bt.set_cookie('taskStatus', true);
				bt.soft.set_lib_config(dataRes.name, dataRes.title, dataRes.version);
			} else {
				var item = {
					name: 'disk_analysis',
					pluginName: 'Disk_analysis',
					ps: 'Quickly analyze disk/Hard disk usage',
					preview: false,
					limit: 'ltd',
					description: ['Check hard disk space', 'Occupancy percentage display'],
					imgSrc: 'https://www.bt.cn/Public/new/plugin/disk_analysis/1.png',
				};
				product_recommend.recommend_product_view(
					item,
					{
						imgArea: ['783px', '718px'],
					},
					'ltd',
					120,
					item.name
				);
				var is_buy = dataRes.endtime < 0 && dataRes.pid > 0;
				$('.buyNow')
					.text(is_buy ? 'Buy now' : 'Install now')
					.unbind('click')
					.click(function () {
						if (is_buy) {
							bt.soft.product_pay_view({
								name: dataRes.title,
								pid: dataRes.pid,
								type: dataRes.type,
								plugin: true,
								renew: -1,
								ps: dataRes.ps,
								ex1: dataRes.ex1,
								totalNum: 120,
							});
						} else {
							bt.soft.install('disk_analysis');
						}
					});
			}
		});
	}
};

// index.get_init();

//setTimeout(function () { index.get_cloud_list() }, 800);

// product_recommend.init(function () {
// 	index.get_product_status(function () {
// 		index.recommend_paid_version();
// 	});
// 	index.get_index_list();
// });
