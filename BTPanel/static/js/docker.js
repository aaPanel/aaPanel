/*
 * @Author: 立夫
 * @Date: 2022-04-02 14:50:32
 * @LastEditTime: 2022-04-20 15:14:58
 * @Description: 
 * @FilePath: \198\BTPanel\static\js\docker.js
 * 可以输入预定的版权声明、个性签名、空行等
 */

$('#cutMode .tabs-item').on('click', function () {
    var type = $(this).data('type'),
        index = $(this).index();
    $(this).addClass('active').siblings().removeClass('active');
    $('.tab-con').find('.tab-con-block').eq(index).removeClass('hide').siblings().addClass('hide');
    
    docker.initTabConfig(type)//初始化tab，获取内容
    bt.set_cookie('docker_model',type)  //Cookie保存当前tab位置
});

var docker = {
    tabName:'container',//当前所处tab位置
    global_api:'/project/docker/model',
    global:{
        url:'unix:///var/run/docker.sock',
        dk_model_name:'',
        dk_def_name:'',
    },
    dk_images:[],   //镜像列表》容器页面专用
    dk_volumes:[],  //卷列表  》容器页面专用
    dk_template:[], //模板列表》容器编排页面专用
    dk_registry:[], //仓库列表》镜像页面专用
    cont_chart:{    //容器图表数据
        cpu_list:[],
        mem_list:{
            usage:[],
            cache:[]
        },
        disk_list:{
            read:[],
            write:[]
        },
        network_list:{
            tx:[],
            rx:[]
        },
        time_list:[]
    },
    cont_chart_id:{  //容器图表dom
        cpu:null,
        mem:null,
        disk:null,
        network:null
    },
    cont_setInterval:null,  //图表定时器
    log_file_setInterval:null, //日志定时器
    log_layer_open:null,    //日志弹窗
    /**
     * @description 获取容器列表
     */
    get_container:function(){
        var that = this;
        var _config = $.extend({},this.global,{dk_def_name:'get_list'})
        var dk_container_table = bt_tools.table({
            el:'#dk_container_table',
            load: true,
            url:this.global_api,
            minWidth: '1050px',
            height:750,
            param: {data:JSON.stringify(_config)},
            dataFilter: function (res) {
                if(!res.msg.installed || !res.msg.service_status) that.stop_user_operation(res.msg.installed,res.msg.service_status)
                that.dk_images = res['msg']['images']
                that.dk_volumes = res['msg']['volumes']
                that.dk_template = res['msg']['template']
                return { data: res['msg']['container_list'] };
            },
            default: lan.docker.public.no_data(lan.docker.public.container),
            column:[{ 
                type: 'checkbox', 
                class: '', 
                width: 20 
            },{
                fid: 'name',
                title: lan.docker.container.name,
                width:146,
                template:function(row){
                    return '<span class="btlink size_ellipsis" style="width:130px" title="'+row.name+'">'+row.name+'</span>'
                },
                event: function (row) {
                    that.open_container_config(row)
                }
            },{
                title: lan.docker.container.status,
                width: 100,
                template:function(row){
                    var _class = '',_icon = '',text = ''
                    switch(row.status){
                        case 'running':
                            _class = 'bt_success'
                            _icon = 'glyphicon-play'
                            text = lan.docker.public.activated
                            break;
                        case 'paused':
                            _class = 'bt_warning'
                            _icon = 'glyphicon-pause'
                            text = lan.docker.public.paused
                            break;
                        default:
                            _class = 'bt_danger'
                            _icon = 'glyphicon-pause'
                            text = lan.docker.public.stopped
                            break;
                    }
                    return '<a class="btlink '+_class+'">'+text+'<span class="glyphicon '+_icon+'"></span></a>'
                },
                event:function(row){
                    if($('.dk_status_select_list').length == 0){
                        $('.dk_status_select').append('\
												<ul class="dk_status_select_list">\
													<li data-key="start">' + lan.docker.container.start + '</li>\
													<li data-key="stop">' + lan.docker.container.stop + '</li>\
													<li data-key="pause">' + lan.docker.container.pause + '</li>\
													<li data-key="unpause">' + lan.docker.container.unpause + '</li>\
													<li data-key="restart">' + lan.docker.container.restart + '</li>\
													<li data-key="reload">' + lan.docker.container.reload + '</li>\
												</ul>');

                        // 事件
                        $('.dk_status_select_list li').click(function(){
                            var _type = $(this).data('key')
                            that.container_status_setting(_type,row.detail.Id,dk_container_table)
                        })

                        // 下拉定位
                        var thLeft = $('#dk_container_table .divtable').scrollLeft(), //当前滚动条位置
                            thTop = $('#dk_container_table .divtable').scrollTop(),   //当前滚动条位置
                            domScrollTop = $(document).scrollTop(),
                            _thSpan = $('.dk_status_select')[0]
                            
                        $('.dk_status_select_list').css({'left':_thSpan.offsetLeft+210-thLeft,'top':(_thSpan.offsetTop+153-domScrollTop-thTop)})
                    }
                }
            },{
                fid: 'image',
                width:160,
                title: lan.docker.container.mirror_image,
                template:function(row){
                    return '<span class="size_ellipsis" style="width:144px" title="'+row.image+'">'+row.image+'</span>'
                }
            },{
                fid:'ip',
                title:'IP',
            },{
                fid:'cpu_usage',
                width: 120,
                title: lan.docker.container.cpu_usage,
                template:function(row){
                    return '<span">'+(row.cpu_usage !== ''?row.cpu_usage+'%':'')+'</span>'
                }
            },{
                fid: 'port',
                title: lan.docker.container.port,
                template:function(row){
                    var _port = []
                    $.each(row.ports,function(index,item){
                        if(item != null){
                            _port.push(item[0]['HostPort']+'-->'+index)
                        }
                    })
                    return '<span>'+_port.join()+'</span>'
                }
            },{
                width: 150,
                title: lan.docker.container.time,
                template:function(row){
                    return '<span>'+that.utc2beijing(row.time)+'</span>'
                }
            },{
                title: lan.public.operate,
                type: 'group',
                width: 300,
                align: 'right',
                group: [{
                    title: lan.docker.container.monitoring,
                    event: function(row){
                        bt_tools.open({
                            type: 1,
                            title: '[' + row.name + '] ' + lan.docker.container.online_monitoring,
                            area: '1100px',
                            btn: false,
                            content: '<div class="pd15 cont-chart-dialog">\
                                <div class="cont_chart_line"><div class="cont_chart_child_title">' + lan.docker.container.basic_information + '</div>\
                                    <div class="">\
                                        <div class="cont_chart_basis"><strong>' + lan.pythonmamager.mem + ': </strong><span>-</span></div>\
                                        <div class="cont_chart_basis"><strong>' + lan.docker.container.flow_situation + ': </strong><span>- / -</span></div>\
                                    </div>\
                                </div>\
                                <div class="cont_chart_block"><div class="cont_chart_child_title">CPU</div><div class=""><div id="cont_cpu" style="width:100%;height:240px"></div></div></div>\
                                <div class="cont_chart_block"><div class="cont_chart_child_title">' + lan.pythonmamager.mem + '</div><div class=""><div id="cont_mem" style="width:100%;height:240px"></div></div></div>\
                                <div class="cont_chart_block"><div class="cont_chart_child_title">' + lan.docker.container.disk + '</div><div class=""><div id="cont_disk" style="width:100%;height:240px"></div></div></div>\
                                <div class="cont_chart_block"><div class="cont_chart_child_title">' + lan.docker.container.network + '</div><div class=""><div id="cont_network" style="width:100%;height:240px"></div></div></div>\
                            </div>',
                            success:function(){
                                // 先初始化数据
                                that.remove_cont_chart_data()
                                //加载图表文件
                                jQuery.ajax({ 
                                    url: "/static/js/echarts.min.js",
                                    dataType: "script",
                                    cache: true
                                }).done(function() {
                                    that.render_cont_chart(row); //默认渲染
                                    that.cont_setInterval = setInterval(function(){
                                        that.transform_cont_chart_data(row);
                                    },3000)//默认三秒获取一次数据
                                });
                            },
                            cancel: function () {
                                that.remove_cont_chart_data()
                            }
                        })
                    }
                },{
                    title: lan.public.terminal,
                    event:function(row){
                        that.open_container_shell_view(row);
                    }
                },{
                    title: lan.docker.container.path,
                    event:function(row){
                        if(row.merged == '') return layer.msg(lan.docker.container.path_not, { icon: 0 }) 
                        openPath(row.merged);
                    }
                },{
                    title: lan.public.log,
                    event:function(row){
											that.ajax_task_method('get_logs',{data:{id:row.detail.Id},tips: lan.docker.container.get_logs_tips },function(res){
												layer.open({
													title:'['+row.name+'] ' + lan.docker.container.log,
													type:1,
													area: '700px',
													shadeClose: false,
													closeBtn: 2,
													btn:false,
													content: '\
													<div class="setchmod bt-form" style="padding: 0">\
														<pre class="dk-container-log" style="overflow: auto; border: 0px none; line-height:23px;padding: 15px; margin: 0px; white-space: pre-wrap; height: 405px; background-color: rgb(51,51,51);color:#f1f1f1;border-radius:0px;font-family: \"微软雅黑\"">' + (res.msg == '' ? lan.docker.container.log_none : res.msg) + '</pre>\
													</div>',
													success:function(){
														$('.dk-container-log').scrollTop($('.dk-container-log').prop('scrollHeight'))
													}
												});
											});
                    }
                },{
									title: lan.public.del,
									event:function(row){
										bt.confirm({
											title: lan.docker.container.del_container + ' [' + row.name + ']',
											msg: lan.docker.container.del_container_msg
										}, function () {
											that.ajax_task_method('del_container',{data:{id:row.detail.Id},tips: lan.docker.container.del_container_tips},function(res){
												if(res.status) that.initTabConfig('container')  //刷新列表
												bt_tools.msg(res)
											})
										});
									}
                }]
            }],
            tootls:[{
                type: 'group',
                positon: ['left', 'top'],
                list: [{
                    title: lan.docker.container.add_container,
                    active: true,
                    event: function () {
                        that.add_container();
                    }
                }]
            },{ // 批量操作
                type: 'batch', //batch_btn
                positon: ['left', 'bottom'],
                placeholder: lan.public.please_choose,
                buttonValue: lan.public.exec,
                disabledSelectValue: lan.docker.container.batch_select_tips,
                selectList: [{
                    title: lan.docker.container.start_container,
                    url: that.global_api,
                    load: true,
                    param:function(crow){
                        return {data:that.batch_param_convert('start',{id:crow.id})}  
                    },
                    refresh: true,
                    callback: function (thatc) { 
                        thatc.start_batch({}, function (list) {
                            var html = ''
                            for (var i = 0; i < list.length; i++) {
                                var item = list[i];
                                html += '<tr><td>' + item.name + '</td><td><div style="float:right;"><span style="color:' + (item.request.status ? '#20a53a' : 'red') + '">' + (item.request.status ? lan.public.setup_success : lan.public.setup_fail) + '</span></div></td></tr>';
                            }
                            dk_container_table.$batch_success_table({
                                title: lan.site.batch_text + lan.docker.container.start_container,
                                th: lan.docker.container.start_container,
                                html: html
                            });
                            dk_container_table.$refresh_table_list(true);
                        });
                    }
                },{
                    title: lan.docker.container.stop_container,
                    url: that.global_api,
                    load: true,
                    param:function(crow){
                        return {data:that.batch_param_convert('stop',{id:crow.id})}  
                    },
                    refresh: true,
                    callback: function (thatc) { 
                        thatc.start_batch({}, function (list) {
                            var html = ''
                            for (var i = 0; i < list.length; i++) {
                                var item = list[i];
                                html += '<tr><td>' + item.name + '</td><td><div style="float:right;"><span style="color:' + (item.request.status ? '#20a53a' : 'red') + '">' + (item.request.status ? lan.public.setup_success : lan.public.setup_fail) + '</span></div></td></tr>';
                            }
                            dk_container_table.$batch_success_table({
                                title: lan.site.batch_text + lan.docker.container.stop_container,
                                th: lan.docker.container.stop_container,
                                html: html
                            });
                            dk_container_table.$refresh_table_list(true);
                        });
                    }
                },{
                    title: lan.docker.container.pause_container,
                    url: that.global_api,
                    load: true,
                    param:function(crow){
                        return {data:that.batch_param_convert('pause',{id:crow.id})}  
                    },
                    refresh: true,
                    callback: function (thatc) { 
                        thatc.start_batch({}, function (list) {
                            var html = ''
                            for (var i = 0; i < list.length; i++) {
                                var item = list[i];
                                html += '<tr><td>' + item.name + '</td><td><div style="float:right;"><span style="color:' + (item.request.status ? '#20a53a' : 'red') + '">' + (item.request.status ? lan.public.setup_success : lan.public.setup_fail) + '</span></div></td></tr>';
                            }
                            dk_container_table.$batch_success_table({
                                title: lan.site.batch_text + lan.docker.container.pause_container,
                                th: lan.docker.container.pause_container,
                                html: html
                            });
                            dk_container_table.$refresh_table_list(true);
                        });
                    }
                },{
                    title: lan.docker.container.unpause_container,
                    url: that.global_api,
                    load: true,
                    param:function(crow){
                        return {data:that.batch_param_convert('unpause',{id:crow.id})}  
                    },
                    refresh: true,
                    callback: function (thatc) { 
                        thatc.start_batch({}, function (list) {
                            var html = ''
                            for (var i = 0; i < list.length; i++) {
                                var item = list[i];
                                html += '<tr><td>' + item.name + '</td><td><div style="float:right;"><span style="color:' + (item.request.status ? '#20a53a' : 'red') + '">' + (item.request.status ? lan.public.setup_success : lan.public.setup_fail) + '</span></div></td></tr>';
                            }
                            dk_container_table.$batch_success_table({
                                title: lan.site.batch_text + lan.docker.container.unpause_container,
                                th: lan.docker.container.unpause_container,
                                html: html
                            });
                            dk_container_table.$refresh_table_list(true);
                        });
                    }
                },{
                    title: lan.docker.container.restart_container,
                    url: that.global_api,
                    load: true,
                    param:function(crow){
                        return {data:that.batch_param_convert('restart',{id:crow.id})}  
                    },
                    refresh: true,
                    callback: function (thatc) { 
                        thatc.start_batch({}, function (list) {
                            var html = ''
                            for (var i = 0; i < list.length; i++) {
                                var item = list[i];
                                html += '<tr><td>' + item.name + '</td><td><div style="float:right;"><span style="color:' + (item.request.status ? '#20a53a' : 'red') + '">' + (item.request.status ? lan.public.setup_success : lan.public.setup_fail) + '</span></div></td></tr>';
                            }
                            dk_container_table.$batch_success_table({
                                title: lan.site.batch_text + lan.docker.container.restart_container,
                                th: lan.docker.container.restart_container,
                                html: html
                            });
                            dk_container_table.$refresh_table_list(true);
                        });
                    }
                },{
                    title: lan.docker.container.reload_container,
                    url: that.global_api,
                    load: true,
                    param:function(crow){
                        return {data:that.batch_param_convert('reload',{id:crow.id})}  
                    },
                    refresh: true,
                    callback: function (thatc) { 
                        thatc.start_batch({}, function (list) {
                            var html = ''
                            for (var i = 0; i < list.length; i++) {
                                var item = list[i];
                                html += '<tr><td>' + item.name + '</td><td><div style="float:right;"><span style="color:' + (item.request.status ? '#20a53a' : 'red') + '">' + (item.request.status ? lan.public.setup_success : lan.public.setup_fail) + '</span></div></td></tr>';
                            }
                            dk_container_table.$batch_success_table({
                                title: lan.site.batch_text + lan.docker.container.reload_container,
                                th: lan.docker.container.reload_container,
                                html: html
                            });
                            dk_container_table.$refresh_table_list(true);
                        });
                    }
                },{
                    title: lan.docker.container.del_container,
                    url: that.global_api,
                    load: true,
                    param:function(crow){
                        return {data:that.batch_param_convert('del_container',{id:crow.id})}  
                    },
                    refresh: true,
                    callback: function (thatc) { 
                        bt.show_confirm(lan.site.batch_text + lan.docker.container.del_container, "<span style='color:red'>" + lan.docker.container.batch_del_container_tips + "</span>", function () {
                        thatc.start_batch({}, function (list) {
                            var html = ''
                            for (var i = 0; i < list.length; i++) {
                                var item = list[i];
                                html += '<tr><td>' + item.name + '</td><td><div style="float:right;"><span style="color:' + (item.request.status ? '#20a53a' : 'red') + '">' + (item.request.status ? lan.public.setup_success : lan.public.setup_fail) + '</span></div></td></tr>';
                            }
                            dk_container_table.$batch_success_table({
                                title: lan.site.batch_text + lan.docker.container.del_container,
                                th: lan.docker.container.del_container,
                                html: html
                            });
                            dk_container_table.$refresh_table_list(true);
                        });
                      });
                    }
                }]
            }],
            success:function(){
                $('#dk_container_table tbody td').unbind('mouseenter').mouseenter(function(e){
                    var _tdSPAN = $(this).find('span:first-child').not('.glyphicon')
                    if(e.target.cellIndex == 2){
                        _tdSPAN.addClass('dk_status_select')
                    }else{
                        _tdSPAN.removeClass('dk_status_select')
                        $('.dk_status_select_list').remove()
                    }
                })
                $('#dk_container_table tbody td').unbind('mouseleave').mouseleave(function(e){
                    var _tdSPAN = $(this).find('span:first-child').not('.glyphicon')
                    _tdSPAN.removeClass('dk_status_select')
                    $('.dk_status_select_list').remove()
                })
            }
        })
    },
    /**
     * @description 获取容器编排列表
     */
    get_compose: function () {
        var that = this;
        var _config = $.extend({},this.global,{dk_def_name:'compose_project_list'})
        var dk_compose_table = bt_tools.table({
            el:'#dk_compose_table',
            load: true,
            url:this.global_api,
            minWidth: '820px',
            height:750,
            param: {data:JSON.stringify(_config)},
            dataFilter: function (res) {
                if(!res.msg.installed || !res.msg.service_status) that.stop_user_operation(res.msg.installed,res.msg.service_status)
                that.dk_template = res['msg']['template']
                return { data: res['msg']['project_list'] };
            },
            default: lan.docker.public.no_data(lan.docker.public.compose),
            column:[{ 
                type: 'checkbox', 
                class: '', 
                width: 20 
            },{
                width:266,
                title: lan.docker.compose.project_name,
                template:function(row){
                    return '<span class="size_ellipsis" style="width:250px" title="'+row.name+'">'+row.name+'</span>'
                }
            },{
                title: lan.docker.compose.container_number,
                template:function(row){
                    return '<span>'+row.container.length+'</span>'
                },
                
            },{
                title: lan.docker.compose.startup_time,
                template:function(row){
									return '<span>'+bt.format_data(row.time)+'</span>'
                }
            },
            {
                fid: 'remark',
                title: lan.one_click.description,
                type: 'input',
                blur: function (row, index, ev, key, thatc) {
                    if (row.remark == ev.target.value) return false;
                    that.ajax_task_method('edit_project_remark',{data:{project_id:row.id,remark:ev.target.value}})
                },
                keyup: function (row, index, ev) {
                  if (ev.keyCode === 13) {
                    $(this).blur();
                  }
                }
            },{
                title: lan.public.operate,
                type: 'group',
                width: 150,
                align: 'right',
                group: [{
                    title: lan.docker.compose.container_list,
                    event:function(dk_cont,index){
											if(dk_cont.container.length == 0) return layer.msg(lan.docker.compose.no_container,{icon:0});
											bt_tools.open({
												title: '['+dk_cont.name+'] ' + lan.docker.compose.container_list,
												area:'1000px',
												content:'<div class="pd20" id="project_compose_table"></div>',
												success:function($layer){
													var project_compose_table = bt_tools.table({
														el:'#project_compose_table',
														url:that.global_api,
														param: {data:JSON.stringify(_config)},
														dataFilter: function (res) {
															var top = ($(window).height() - $layer.height()) / 2;
															$layer.css({ 'top': top + 'px' });
															return { data: res['msg']['project_list'][index]['container'] };
														},
														column:[
														{
																fid: 'name',
																title: lan.docker.container.name,
																template:function(row){
																		return '<span class="size_ellipsis" style="width:120px" title="'+row.name+'">'+row.name+'</span>'
																}
														},{
																title: lan.docker.container.status,
																width: 100,
																template:function(row){
																		var _class = '',_icon = '',text = ''
																		switch(row.status){
																				case 'running':
																						_class = 'bt_success'
																						_icon = 'glyphicon-play'
																						text = lan.docker.public.activated
																						break;
																				case 'paused':
																						_class = 'bt_warning'
																						_icon = 'glyphicon-pause'
																						text = lan.docker.public.paused
																						break;
																				default:
																						_class = 'bt_danger'
																						_icon = 'glyphicon-pause'
																						text = lan.docker.public.stopped
																						break;
																		}
																		return '<a class="btlink '+_class+'">'+text+'<span class="glyphicon '+_icon+'"></span></a>'
																},
																event:function(row){
																		if($('.dk_status_select_list').length == 0){
																				$('.dk_status_select').append('<ul class="dk_status_select_list"><li data-key="start">' + lan.docker.container.start + '</li><li data-key="stop">' + lan.docker.container.stop + '</li><li data-key="pause">' + lan.docker.container.pause + '</li><li data-key="unpause">' + lan.docker.container.unpause + '</li><li data-key="restart">' + lan.docker.container.restart + '</li><li data-key="reload">' + lan.docker.container.reload + '</li></ul>')
																				
																				//事件
																				$('.dk_status_select_list li').click(function(){
																						var _type = $(this).data('key')
																						that.container_status_setting(_type,row.detail.Id,project_compose_table,'project')
																				})
								
																				//下拉定位
																				var thLeft = $('#project_compose_table .divtable').scrollLeft(), //当前滚动条位置
																						_thSpan = $('.dk_status_select')[0]
																				$('.dk_status_select_list').css({'left':_thSpan.offsetLeft+20-thLeft,'top':_thSpan.offsetTop+120})
																		}
																}
														},{
																fid: 'image',
																width:110,
																title: lan.docker.container.mirror_image,
																template:function(row){
																		return '<span class="size_ellipsis" style="width:84px" title="'+row.image+'">'+row.image+'</span>'
																}
														},{
																width:150,
																title: lan.docker.container.time,
																template:function(row){
																		return '<span>'+that.utc2beijing(row.time)+'</span>'
																}
														},{
																fid:'ip',
																width:116,
																title:'IP',
																template:function(row){
																		return '<span class="size_ellipsis" style="width:100px" title="'+row.ip+'">'+row.ip+'</span>'
																}
														},{
																fid:'port',
																width: 180,
																title: lan.docker.container.port,
																template:function(row){
																		var _port = []
																		$.each(row.ports,function(index,item){
																				if(item != null){
																						_port.push(item[0]['HostPort']+'-->'+index)
																				}
																		})
																		return '<span class="size_ellipsis" style="width:92px" title="'+_port.join()+'">'+_port.join()+'</span>'
																}
														},{
																title: lan.public.operate,
																type: 'group',
																width: 180,
																align: 'right',
																group: [{
																		title: lan.public.terminal,
																		event:function(row){
																				that.open_container_shell_view(row);
																		}
																},{
																	title: lan.public.log,
																	event:function(row){
																		that.ajax_task_method('get_logs', {
																			data:{id:row.detail.Id},
																			tips: lan.docker.container.get_logs_tips,
																			model_name: {dk_model_name:'container'}
																		},function(res){
																			layer.open({
																				type:1,
																				title:'['+row.name+'] ' + lan.docker.container.log,
																				area: '700px',
																				shadeClose: false,
																				closeBtn: 2,
																				btn:false,
																				content: '<div class="setchmod bt-form"  style="padding: 0">'
																						+ '<pre class="dk-container-log" style="overflow: auto; border: 0px none; line-height:23px;padding: 15px; margin: 0px; white-space: pre-wrap; height: 405px; background-color: rgb(51,51,51);color:#f1f1f1;border-radius:0px;font-family: \"微软雅黑\"">' + (res.msg == '' ? lan.docker.container.log_none : res.msg) + '</pre>'
																						+'</div>',
																				success:function(){
																						$('.dk-container-log').scrollTop(100000000000)
																				}
																			})
																		})
																	}
																},{
																		title: lan.docker.container.path,
																		event:function(row){
																				if(row.merged == '') return layer.msg(lan.docker.container.path_not,{icon:0}) 
																				openPath(row.merged);
																		}
																},{
																		title: lan.public.del,
																		event:function(row){
																				bt.confirm({
																						title: lan.docker.container.del_container + ' [' + row.name + ']',
																						msg: lan.docker.container.del_container_msg
																				}, function () {
																						that.ajax_task_method('del_container',{data:{id:row.detail.Id},tips:lan.docker.container.del_container_tips,model_name:{dk_model_name:'container'}},function(res){
																								if(res.status) project_compose_table.$refresh_table_list(true)  //刷新列表
																								bt_tools.msg(res)
																						})
																				});
																		}
																}]
														}],
														tootls:false,
														success:function(){
																$('#project_compose_table tbody td').unbind('mouseenter').mouseenter(function(e){
																		var _tdSPAN = $(this).find('span:first-child').not('.glyphicon')
																		if(e.target.cellIndex == 1){
																				_tdSPAN.addClass('dk_status_select')
																		}else{
																				_tdSPAN.removeClass('dk_status_select')
																				$('.dk_status_select_list').remove()
																		}
																})
																$('#project_compose_table tbody td').unbind('mouseleave').mouseleave(function(e){
																		var _tdSPAN = $(this).find('span:first-child').not('.glyphicon')
																		_tdSPAN.removeClass('dk_status_select')
																		$('.dk_status_select_list').remove()
																})
																if($('#project_compose_table .tootls_group.tootls_top').length == 0){
																		$('#project_compose_table').prepend('<div class="tootls_group tootls_top"><div class="pull-left"><span>Compose ' + lan.public.operate + ': <span><select class="bt-input-text ml5" style="width:130px" name="set_project_status"><option value="start">' + lan.docker.container.start + ' Compose</option><option value="stop">' + lan.docker.container.stop + ' Compose</option><option value="pause">' + lan.docker.container.pause + ' Compose</option><option value="unpause">' + lan.docker.container.unpause + '</option><option value="restart">' + lan.docker.container.restart + ' Compose</option></select></div>')

																		$('[name=set_project_status]').change(function(){
																				that.ajax_task_method($(this).val(),{data:{project_id:dk_cont.id},tips:$('[name=set_project_status]').find('option:selected').text()},function(res){
																						if(res.status) project_compose_table.$refresh_table_list(true)
																						bt_tools.msg(res)
																				})
																		})
																}
														}
													});
												}
											})
                    }
                },{
									title: lan.public.del,
									event:function(row){
										bt.confirm({
											title: lan.docker.compose.del_compose + ' [' + row.name + ']',
											msg: lan.docker.compose.del_compose_tips
										}, function () {
											that.ajax_task_method('remove', {
												data: { project_id: row.id },
												tips: lan.docker.compose.deleting_compose
											}, function(res){
												if (res.status) that.initTabConfig('compose')  // 刷新列表
												bt_tools.msg(res);
											})
										});
									}
                }]
            }],
            tootls:[{
                type: 'group',
                positon: ['left', 'top'],
                list: [{
                    title: lan.docker.compose.add_btn,
                    active: true,
                    event: function () {
                        that.add_project();
                    }
                }]
            },{ // 批量操作
                type: 'batch', //batch_btn
                positon: ['left', 'bottom'],
                placeholder: lan.public.please_choose,
                buttonValue: lan.public.exec,
                disabledSelectValue: lan.docker.compose.batch_select_tips,
                selectList: [{
                    title: lan.public.del + " compose",
                    url: that.global_api,
                    load: true,
                    param:function(crow){
                        return {data:that.batch_param_convert('remove',{project_id:crow.id})}  
                    },
                    refresh: true,
                    callback: function (thatc) { 
                        bt.show_confirm(lan.docker.compose.batch_del_compose, "<span style='color:red'>" + lan.docker.compose.batch_del_tips + "</span>", function () {
                        thatc.start_batch({}, function (list) {
                            var html = ''
                            for (var i = 0; i < list.length; i++) {
                                var item = list[i];
                                html += '<tr><td>' + item.name + '</td><td><div style="float:right;"><span style="color:' + (item.request.status ? '#20a53a' : 'red') + '">' + (item.request.status ? lan.public.setup_success : lan.public.setup_fail) + '</span></div></td></tr>';
                            }
                            dk_compose_table.$batch_success_table({
                                title: lan.docker.compose.batch_del_compose,
                                th: 'compose',
                                html: html
                            });
                            dk_compose_table.$refresh_table_list(true);
                        });
                      });
                    }
                }]
            }]
        })
    },
    /**
     * @description 获取compose模板列表
     */
    get_model:function(){
        var that = this;
        var _config = $.extend({},this.global,{dk_def_name:'template_list'})
        var dk_model_table = bt_tools.table({
            el:'#dk_model_table',
            load: true,
            url:this.global_api,
            minWidth: '980px',
            height:750,
            param: {data:JSON.stringify(_config)},
            dataFilter: function (res) {
                if(!res.msg.installed || !res.msg.service_status) that.stop_user_operation(res.msg.installed,res.msg.service_status)
                return { data: res['msg']['template'] };
            },
            default: lan.docker.public.no_data(lan.docker.public.compose_template),
            column:[{ 
                type: 'checkbox', 
                class: '', 
                width: 20 
            },
            {
                fid: 'name',
                width: 266,
                title: lan.docker.compose_template.template_name,
                template:function(row){
                    return '<span class="size_ellipsis" style="width:250px" title="'+row.name+'">'+row.name+'</span>'
                }
            },
            {
                width: 266,
                title: lan.site.path,
                template:function(row){
                    return '<a class="btlink size_ellipsis" style="width:250px" title="'+row.path+'">'+row.path+'</a>'
                },
                event: function (row) {
                    openEditorView(0,row.path)
                }
            },
            {
                fid: 'remark',
                title: lan.one_click.description,
                type: 'input',
                blur: function (row, index, ev, key, thatc) {
                    if (row.remark == ev.target.value) return false;
                    that.ajax_task_method('edit_template_remark',{data:{templates_id:row.id,remark:ev.target.value}})
                },
                keyup: function (row, index, ev) {
                  if (ev.keyCode === 13) {
                    $(this).blur();
                  }
                }
            },
            {
                title: lan.public.operate,
                type: 'group',
                width: 200,
                align: 'right',
                group: [{
									title: lan.public.edit,
									event:function(row){
										that.ajax_task_method('get_template', {
											data: { id: row.id },
											tips: lan.docker.compose_template.getting_template
										}, function (res) {
											if (res.status) {
												that.edit_model_view($.extend({content:res['msg']},row))
											}
										});
									}
                },{
                    title: lan.docker.compose_template.pull_mirror_image,
                    event:function(row){
                        that.get_log_situation()
                        that.ajax_task_method('pull',{data:{template_id:row.id},tips:false},function(res){
                            that.remove_log_clearinterval();
                            bt_tools.msg(res);
                        })
                    }
                },{
                    title: lan.public.del,
                    event:function(row){
											bt.confirm({
													title: lan.docker.compose_template.del_template + ' [' + row.name + ']',
													msg: lan.docker.compose_template.del_template_tips
											}, function () {
												that.ajax_task_method('remove_template',{
													data: { template_id: row.id },
													tips: lan.docker.compose_template.del_template
												},function(res){
													bt_tools.msg(res);
													that.initTabConfig('model')  //刷新列表
												})
											});
                    }
                }]
            }],
            tootls:[{
                type: 'group',
                positon: ['left', 'top'],
                list: [{
                    title: lan.public.add,
                    active: true,
                    event: function (ev) {
                        that.add_model_view();
                    }
                }]
            },{ // 批量操作
                type: 'batch', //batch_btn
                positon: ['left', 'bottom'],
                placeholder: lan.public.please_choose,
                buttonValue: lan.public.exec,
                disabledSelectValue: lan.docker.compose_template.batch_select_tips,
                selectList: [
									{
                    title: lan.docker.compose_template.del_template,
                    url: that.global_api,
                    load: true,
                    param:function(crow){
                        return {data:that.batch_param_convert('remove_template',{template_id:crow.id})}  
                    },
                    refresh: true,
                    callback: function (thatc) { 
                        bt.show_confirm(lan.docker.compose_template.batch_del_template, "<span style='color:red'>" + lan.docker.compose_template.batch_del_tips + "</span>", function () {
                        thatc.start_batch({}, function (list) {
                            var html = ''
                            for (var i = 0; i < list.length; i++) {
                                var item = list[i];
                                html += '<tr><td>' + item.name + '</td><td><div style="float:right;"><span style="color:' + (item.request.status ? '#20a53a' : 'red') + '">' + (item.request.status ? lan.public.setup_success : lan.public.setup_fail) + '</span></div></td></tr>';
                            }
                            dk_model_table.$batch_success_table({
                                title: lan.docker.compose_template.batch_del_template,
                                th: lan.docker.compose_template.template_name,
                                html: html
                            });
                            dk_model_table.$refresh_table_list(true);
                        });
                      });
                    }
                	}
								]
            }]
        })
    },
    /**
     * @description 获取网络列表
     */
    get_network:function(){
        var that = this;
        var _config = $.extend({},this.global,{dk_def_name:'get_host_network'})
        var dk_network_table = bt_tools.table({
            el:'#dk_network_table',
            load: true,
            url:this.global_api,
            param: {data:JSON.stringify(_config)},
            height:750,
            dataFilter: function (res) {
                if(!res.msg.installed || !res.msg.service_status) that.stop_user_operation(res.msg.installed,res.msg.service_status)
                return { data: res['msg']['network'] };
            },
            default: lan.docker.public.no_data(lan.docker.public.network),
            column:[{ 
                type: 'checkbox', 
                class: '', 
                width: 20 
            },
            {
                width:266,
                title: lan.docker.network.name,
                template:function(row){
                    return '<span class="size_ellipsis" style="width:250px" title="'+row.name+'">'+row.name+'</span>'
                }
            },
            {fid:'driver',title: lan.docker.network.show},
            {fid:'subnet',title: lan.docker.network.num},
            {fid:'gateway',title: lan.docker.network.gateway},
            {
                width:226,
                title: lan.docker.container.tag,
                template:function(row){
                    var _label = []
                    if(!$.isEmptyObject(row.labels)){
                        $.each(row.labels,function(index,item){
                            _label.push(index+'-'+item)
                        })
                    }
                    return '<span class="size_ellipsis" style="width:210px">'+_label.join() +'</span>'
                }
            },
            {
                width:150,
                title: lan.docker.image.creation_time,
                template:function(row){
                    return '<span>'+that.utc2beijing(row.time)+'</span>'
                }
            },
            {
                title: lan.public.operate,
                type: 'group',
                width: 60,
                align: 'right',
                group: [{
									title: lan.public.del,
									event:function(row){
										bt.confirm({
												title: lan.docker.network.del(row.name),
												msg: lan.docker.network.del_tips
										}, function () {
											that.ajax_task_method('del_network', {
												data: { id: row.id },
												tips: lan.docker.network.deleting
											},function(res){
												if(res.status) that.initTabConfig('network')  //刷新列表
												bt_tools.msg(res);
											})
										});
									}
                }]
            }],
            tootls:[{
                type: 'group',
                positon: ['left', 'top'],
                list: [{
                    title: lan.docker.network.add,
                    active: true,
                    event: function (ev) {
                        that.add_network();
                    }
                }]
            },{ // 批量操作
                type: 'batch', //batch_btn
                positon: ['left', 'bottom'],
                placeholder: lan.public.please_choose,
                buttonValue: lan.public.exec,
                disabledSelectValue: lan.docker.public.batch_select_tips(lan.docker.public.network),
                selectList: [{
                    title: lan.docker.network.del(),
                    url: that.global_api,
                    load: true,
                    param:function(crow){
                        return {data:that.batch_param_convert('del_network',{id:crow.id})}  
                    },
                    refresh: true,
                    callback: function (thatc) { 
                        bt.show_confirm(lan.docker.public.batch_del(lan.docker.public.network), "<span style='color:red'>" + lan.docker.public.batch_del_tips(lan.docker.public.network) + "</span>", function () {
                        thatc.start_batch({}, function (list) {
                            var html = ''
                            for (var i = 0; i < list.length; i++) {
                                var item = list[i];
                                html += '<tr><td>' + item.name + '</td><td><div style="float:right;"><span style="color:' + (item.request.status ? '#20a53a' : 'red') + '">' + (item.request.status ? lan.public.setup_success : lan.public.setup_fail) + '</span></div></td></tr>';
                            }
                            dk_network_table.$batch_success_table({
                                title: lan.docker.public.batch_del(lan.docker.public.network),
                                th: lan.docker.network.name,
                                html: html
                            });
                            dk_network_table.$refresh_table_list(true);
                        });
                      });
                    }
                }]
            }]
        })
    },
    /**
     * @description 获取存储卷列表
     */
    get_volume:function(){
        var that = this;
        var _config = $.extend({},this.global,{dk_def_name:'get_volume_list'})
        var dk_volume_table = bt_tools.table({
            el:'#dk_volume_table',
            load: true,
            url:this.global_api,
            minWidth: '1020px',
            height:750,
            param: {data:JSON.stringify(_config)},
            dataFilter: function (res) {
                if(!res.msg.installed || !res.msg.service_status) that.stop_user_operation(res.msg.installed,res.msg.service_status)
                return { data: res['msg']['volume'] };
            },
            default: lan.docker.public.no_data(lan.docker.public.volume),
            column:[{ 
                type: 'checkbox', 
                class: '', 
                width: 20 
            },
            {fid:'Name',width:216,title: lan.docker.public.volume,template:function(row){
                return '<span class="size_ellipsis" style="width:200px" title="'+row.Name+'">'+row.Name+'</span>'
            }},
            {
                type: 'link',
                title: lan.docker.volume.mount,
                template:function(row){
                    return '<a class="btlink size_ellipsis" style="width:250px" title="'+row.Mountpoint+'">'+row.Mountpoint+'</a>'
                },
                event: function (row) {
                    openPath(row.Mountpoint);
                }
            },
            {
                fid:'container',
                title: lan.docker.public.container
            },
            {fid: 'Driver',title: lan.docker.volume.driver},
            {
                fid:'CreatedAt',
                width:150,
                title: lan.docker.public.creation_time,
                template:function(row){
                    return '<span>'+that.utc2beijing(row.CreatedAt)+'</span>'
                }
            },
            {
                width:206,
                title: lan.docker.public.tag,
                template:function(row){
                    var _label = []
                    if(!$.isEmptyObject(row.Labels)){
                        $.each(row.Labels,function(index,item){
                            _label.push(index+'-'+item)
                        })
                    }
                    return '<span class="size_ellipsis" style="width:190px">'+_label.join() +'</span>'
                }
            },
            {
                title: lan.public.operate,
                type: 'group',
                width: 60,
                align: 'right',
                group: [{
                    title: lan.public.del,
                    event:function(row){
                        bt.confirm({
                            title: lan.docker.volume.del(row.Name),
                            msg: lan.docker.public.del_tips(lan.docker.public.volume)
                        }, function () {
                            that.ajax_task_method('remove',{data:{name:row.Name},tips:lan.docker.volume.deleting},function(res){
                                if(res.status)that.initTabConfig('volume')  //刷新列表
                                bt_tools.msg(res);
                                
                            })
                        });
                    }
                }]
            }],
            tootls:[{
                type: 'group',
                positon: ['left', 'top'],
                list: [{
                    title: lan.docker.volume.add,
                    active: true,
                    event: function (ev) {
                        that.add_volume();
                    }
                }]
            },{ // 批量操作
                type: 'batch', //batch_btn
                positon: ['left', 'bottom'],
                placeholder: lan.public.please_choose,
                buttonValue: lan.public.exec,
                disabledSelectValue: lan.docker.public.batch_select_tips(lan.docker.public.volume),
                selectList: [{
                    title: lan.docker.volume.del(),
                    url: that.global_api,
                    load: true,
                    param:function(crow){
                        return {data:that.batch_param_convert('remove',{name:crow.Name})}  
                    },
                    refresh: true,
                    callback: function (thatc) { 
                        bt.show_confirm(lan.docker.public.batch_del(lan.docker.public.volume), "<span style='color:red'>" + lan.docker.public.batch_del_tips(lan.docker.public.volume) + "</span>", function () {
                        thatc.start_batch({}, function (list) {
                            var html = ''
                            for (var i = 0; i < list.length; i++) {
                                var item = list[i];
                                html += '<tr><td>' + item.name + '</td><td><div style="float:right;"><span style="color:' + (item.request.status ? '#20a53a' : 'red') + '">' + (item.request.status ? lan.public.setup_success : lan.public.setup_fail) + '</span></div></td></tr>';
                            }
                            dk_volume_table.$batch_success_table({
                                title: lan.docker.public.batch_del(lan.docker.public.volume),
                                th: lan.docker.volume.name,
                                html: html
                            });
                            dk_volume_table.$refresh_table_list(true);
                        });
                      });
                    }
                }]
            }]
        })
    }, 
    /**
     * @description 获取仓库列表
     */
    get_registry:function(){
        var that = this;
        var _config = $.extend({},this.global,{dk_def_name:'registry_list'})
        var dk_registry_table = bt_tools.table({
            el:'#dk_registry_table',
            load: true,
            url:this.global_api,
            height:750,
            param: {data:JSON.stringify(_config)},
            dataFilter: function (res) {
                if(!res.msg.installed || !res.msg.service_status) that.stop_user_operation(res.msg.installed,res.msg.service_status)
                return { data: res['msg']['registry'] };
            },
            default: lan.docker.public.no_data(lan.docker.public.repository),
            column:[{ 
                type: 'checkbox', 
                class: '', 
                width: 20 
            },
            {width:266,title: 'URL',template:function(row){
                return '<span class="size_ellipsis" style="width:250px">'+row.url+'</span>'
            }},
            {fid: 'username',title: lan.docker.repository.username },
            {fid: 'name',title: lan.docker.repository.name },
            {
                fid: 'remark',
                title: lan.one_click.description,
                type: 'input',
                blur: function (row, index, ev, key, thatc) {
                    if (row.remark == ev.target.value) return false;
                    row['remark'] = ev.target.value
                    row['registry'] = row.url
                    that.ajax_task_method('edit',{data:row})
                },
                keyup: function (row, index, ev) {
                  if (ev.keyCode === 13) {
                    $(this).blur();
                  }
                }
            },
            {
                title: lan.public.operate,
                type: 'group',
                width: 100,
                align: 'right',
                group: [{
                    title: lan.public.edit,
                    event:function(row){
                        that.render_registry_view(row);
                    }
                },{
                    title: lan.public.del,
                    event:function(row){
                        bt.confirm({
                            title: lan.docker.repository.del(row.name),
                            msg: lan.docker.public.del_tips(lan.docker.public.repository)
                        }, function () {
                            that.ajax_task_method('remove',{data:{id:row.id},tips: lan.docker.repository.deleting},function(res){
                                bt_tools.msg(res);
                                that.initTabConfig('registry')  //刷新列表
                            })
                        });
                    }
                }]
            }],
            tootls:[{
                type: 'group',
                positon: ['left', 'top'],
                list: [{
                    title: lan.docker.repository.add,
                    active: true,
                    event: function (ev) {
                        that.render_registry_view();
                    }
                }]
            },{ // 批量操作
                type: 'batch', //batch_btn
                positon: ['left', 'bottom'],
                placeholder: lan.public.please_choose,
                buttonValue: lan.public.exec,
                disabledSelectValue: lan.docker.public.batch_select_tips(lan.docker.public.repository),
                selectList: [{
                    title: lan.docker.repository.del(),
                    url: that.global_api,
                    load: true,
                    param:function(crow){
                        return {data:that.batch_param_convert('remove',{id:crow.id})}  
                    },
                    refresh: true,
                    callback: function (thatc) { 
                        bt.show_confirm(lan.docker.public.batch_del(lan.docker.public.repository), "<span style='color:red'>" + lan.docker.public.batch_del_tips(lan.docker.public.repository) + "</span>", function () {
                        thatc.start_batch({}, function (list) {
                            var html = ''
                            for (var i = 0; i < list.length; i++) {
                                var item = list[i];
                                html += '<tr><td>' + item.name + '</td><td><div style="float:right;"><span style="color:' + (item.request.status ? '#20a53a' : 'red') + '">' + (item.request.status ? lan.public.setup_success : lan.public.setup_fail) + '</span></div></td></tr>';
                            }
                            dk_registry_table.$batch_success_table({
                                title: lan.docker.public.batch_del(lan.docker.public.repository),
                                th: lan.docker.repository.name,
                                html: html
                            });
                            dk_registry_table.$refresh_table_list(true);
                        });
                      });
                    }
                }]
            }]
        })
    },
    /**
     * @description 获取镜像列表
     */
    get_image:function(){
        var that = this;
        var _config = $.extend({},this.global,{dk_def_name:'image_list'})
        var dk_image_table = bt_tools.table({
            el:'#dk_image_table',
            load: true,
            url:this.global_api,
            minWidth: '1020px',
            height:750,
            param: {data:JSON.stringify(_config)},
            dataFilter: function (res) {
                if(!res.msg.installed || !res.msg.service_status) that.stop_user_operation(res.msg.installed,res.msg.service_status)
                that.dk_registry = res['msg']['registry_list']
                return { data: res['msg']['images_list'] };
            },
            default: lan.docker.public.no_data(lan.docker.public.mirror_image),
            column:[{ 
                type: 'checkbox', 
                class: '', 
                width: 20 
            },
            {
                width:200,
                title: 'ID',
                template:function(row){
                    return '<span class="size_ellipsis" style="width:184px" title="'+row.id+'">'+row.id+'</span>'
                }
            },
            {
                fid: 'name',
                title: lan.docker.image.name
            },
            {
                width:86,
                title: lan.database.size,
                template: function (row) {
                    return '<span>'+bt.format_size(row.size)+'</span>'
                }
            },
            {
                width:150,
                title: lan.docker.image.creation_time,
                template:function(row){
                    return '<span>'+that.utc2beijing(row.time)+'</span>'
                }
            },
            {
                title: lan.public.operate,
                type: 'group',
                width: 140,
                align: 'right',
                group: [{
                    title: lan.docker.image.push,
                    event:function(row){
                        var _registry = []
                        if(that.dk_registry.length > 0){
                            $.each(that.dk_registry,function(index,item){
                                _registry.push({title:item.name+'['+item.url+'/'+item.namespace+']',value:item.name})
                            })
                        }else{
                            _registry = [{title: lan.docker.image.push_tips1,value:'dk_registry_false'}]
                        }
                        bt_tools.open({
                            type: 1,
                            title: lan.docker.image.push_title1 + ' [' + row.name + '] ' + lan.docker.image.push_title2,
                            area: '580px',
                            btn: [lan.public.submit, lan.site.no],
                            content: {
                                'class': "pd20",
                                form: [{
                                    label: lan.docker.image.warehouse_name,
                                    group: {
                                        name:'name',
                                        type:'select',
                                        width: "400px",
                                        list:_registry
                                    }
                                },{
                                    label: lan.docker.container.tag,
                                    group: {
                                        name: "tag",
                                        type: "text",
                                        value: '',
                                        width: "400px",
                                        placeholder: lan.docker.image.tag_input
                                    }
                                }]
                            },
                            yes: function (formD,indexs) {
                                if (formD.name === 'dk_registry_false') return bt_tools.msg(lan.docker.image.push_tips2, 2)
                                if (formD.tag === '') return bt_tools.msg(lan.docker.image.push_tips3, 2)
                                formD['id'] = row.id
                                that.get_log_situation()
                                that.ajax_task_method('push',{data:formD,tips:false},function(res){
                                    that.remove_log_clearinterval();
                                    if(res.status){
                                        layer.closeAll();
                                        that.initTabConfig('image')  //刷新列表
                                    }
                                    bt_tools.msg(res)
                                })
                            }
                        })
                    }
                },{
                    title: lan.docker.image.export,
                    event:function(row){
                        bt_tools.open({
                            type: 1,
                            title: lan.docker.image.export_title(row.name),
                            area: '480px',
                            btn: [lan.docker.image.export, lan.site.no],
                            content: {
                                'class': "pd20",
                                form: [{
                                    label: lan.site.path,
                                    group: {
                                        name: "path",
                                        type: "text",
                                        value: '',
                                        width: "240px",
                                        placeholder: lan.docker.image.path_input,
                                        icon: {
                                            type: 'glyphicon-folder-open',
                                            event:function(){}
                                        }
                                    }
                                },{
                                    label: lan.files.file_name,
                                    group: {
                                        name: "name",
                                        type: "text",
                                        value: '',
                                        width: "240px",
                                        placeholder: lan.docker.image.file_input,
                                        unit:'.tar'
                                    }
                                }]
                            },
                            yes: function (formD,indexs) {
															if (formD.path === '') return bt_tools.msg(lan.docker.image.export_tips1, 2)
															if (formD.name === '') return bt_tools.msg(lan.docker.image.export_tips, 2)
															formD['id'] = row.id
															
															that.ajax_task_method('save', {
																data: formD,
																tips: lan.docker.image.exporting
															}, function(res){
																if(res.status){
																	layer.close(indexs);
																	that.initTabConfig('image')  //刷新列表
																}
																bt_tools.msg(res)
															})
                            }
                        })
                    }
                },{
                    title: lan.public.del,
                    event:function(row){
											bt.confirm({
												title: lan.docker.image.del(row.name),
												msg: lan.docker.image.del_tips
											}, function () {
												that.ajax_task_method('remove', {
													data: {
														id: row.id, force: 0, name: row.name
													},
													tips: lan.docker.image.deleting
												}, function (res) {
													if (res.status) that.initTabConfig('image')  //刷新列表
													bt_tools.msg(res);
												})
											});
                    }
                }]
            }],
            tootls:[{
                type: 'group',
                positon: ['left', 'top'],
                list: [{
                    title: lan.docker.image.btn1,
                    active: true,
                    event:function(ev){
                        var _registry = []
                        if(that.dk_registry.length > 0){
													$.each(that.dk_registry,function(index,item){
														_registry.push({title:item.name+'['+item.url+'/'+item.namespace+']',value:item.name})
													})
                        }else{
													_registry = [{title:lan.docker.image.warehouse_select,value:'dk_registry_false'}]
                        }
                        bt_tools.open({
                            type: 1,
                            title: lan.docker.image.pull_title,
                            area: '580px',
                            btn: [lan.public.submit, lan.site.no],
                            content: {
                                'class': "pd20",
                                form: [{
                                    label: lan.docker.image.warehouse_name,
                                    group: {
                                        name:'name',
                                        type:'select',
                                        width: "400px",
                                        list:_registry
                                    }
                                },{
                                    label: lan.docker.image.mirror_name,
                                    group: {
                                        name: "image",
                                        type: "text",
                                        value: '',
                                        width: "400px",
                                        placeholder: lan.docker.image.mirror_input
                                    }
                                }]
                            },
                            yes: function (formD, indexs) {
                                if (formD.name === 'dk_registry_false') return bt_tools.msg(lan.docker.image.pull_tips1, 2)
                                if (formD.image === '') return bt_tools.msg(lan.docker.image.pull_tips2, 2)
                                that.get_log_situation()
                                that.ajax_task_method('pull_from_some_registry',{data:formD,tips:false},function(res){
                                    that.remove_log_clearinterval()
                                    if(res.status){
                                        layer.close(indexs);
                                        that.initTabConfig('image')  //刷新列表
                                    }
                                    bt_tools.msg(res)
                                })
                            }
                        })
                    }
                },{
                    title: lan.docker.image.btn2,
                    event:function(ev){
                        bt_tools.open({
                            type: 1,
                            title: lan.docker.image.btn2,
                            area: '460px',
														btn: [lan.docker.image.import, lan.site.no],
                            content: {
                                'class': "pd20",
                                form: [{
                                    label: lan.site.path,
                                    group: {
                                        name: "path",
                                        type: "text",
                                        value: '',
                                        width: "240px",
                                        placeholder: lan.docker.image.path_input,
                                        icon: {
                                            type: 'glyphicon-folder-open',
                                            select:'file',
                                            event:function(){}
                                        }
                                    }
                                }]
                            },
                            yes: function (formD, indexs) {
                                if (formD.path === '') return bt_tools.msg(lan.docker.image.export_tips1, 2);
                                that.ajax_task_method('load',{data:formD,tips: lan.docker.image.importing},function(res){
                                    if(res.status){
                                        layer.close(indexs);
                                        that.initTabConfig('image')  //刷新列表
                                    }
                                    bt_tools.msg(res)
                                })
                            }
                        })
                    }
                },{
                    title: lan.docker.image.btn3,
                    event: function () {
                        that.construction_image();
                    }
                }]
            },{ // 批量操作
                type: 'batch', //batch_btn
                positon: ['left', 'bottom'],
                placeholder: lan.public.please_choose,
                buttonValue: lan.public.exec,
                disabledSelectValue: lan.docker.image.batch_tips,
                selectList: [{
                    title: lan.docker.image.del(),
                    url: that.global_api,
                    load: true,
                    param:function(crow){
                        return {data:that.batch_param_convert('remove',{id:crow.id,force:0,name:crow.name})}  
                    },
                    refresh: true,
                    callback: function (thatc) { 
                        bt.show_confirm(lan.docker.image.batch_del, "<span style='color:red'>" + lan.docker.image.batch_del_tips + "</span>", function () {
                        thatc.start_batch({}, function (list) {
                            var html = ''
                            for (var i = 0; i < list.length; i++) {
                                var item = list[i];
                                html += '<tr><td>' + item.name + '</td><td><div style="float:right;"><span style="color:' + (item.request.status ? '#20a53a' : 'red') + '">' + (item.request.status ? lan.public.setup_success : lan.public.setup_fail) + '</span></div></td></tr>';
                            }
                            dk_image_table.$batch_success_table({
                                title: lan.docker.image.batch_del,
                                th: lan.docker.image.name,
                                html: html
                            });
                            dk_image_table.$refresh_table_list(true);
                        });
                      });
                    }
                }]
            }]
        })
    },
    /**
     * @description 获取设置页面
     */
    get_setup:function(){
        var _html = '',that = this;
        this.ajax_task_method('get_config',{},function(res){
            var info = res.msg;
            var status_info = info.service_status ? ['Enable', '#20a53a', 'play'] : ['Stopped', 'red', 'pause'];
            
            _html = '<div class="bt-form">\
                <div class="line">\
                    <span class="tname">Docker server: </span>\
                    <div class="info-r"><div style="height: 33px;line-height: 33px;display: inline-block;">Current status: <span>' + status_info[0] + '</span><span style="color:' + status_info[1] + '; margin-left: 3px;" class="glyphicon glyphicon glyphicon-' + status_info[2] + '"></span></div><div style="display: inline-block;margin-left: 49px;">\
                        <button class="btn btn-default btn-sm serveSetup" data-setup="'+(info.service_status?'stop':'start')+'">'+(info.service_status?'Stop':'Start up')+'</button>\
                        <button class="btn btn-default btn-sm serveSetup" data-setup="restart">Restart</button>\
                    </div></div>\
                </div>\
                <div class="line">\
                    <span class="tname">Container monitor: </span>\
                    <div class="info-r">\
                        <div class="inlineBlock mr50" style="margin-top: 5px;vertical-align: -6px;">\
                            <input class="btswitch btswitch-ios" id="monitor_status" type="checkbox" name="monitor">\
                            <label class="btswitch-btn" for="monitor_status" style="margin-bottom: 0;"></label>\
                        </div>\
                        <span class="unit">* Set the container page monitoring switch. After this switch is turned off, the CPU usage will not be monitored.</span>\
                    </div>\
                </div>\
                <div class="line">\
                    <span class="tname">Save days: </span>\
                    <div class="info-r">\
                        <input class="bt-input-text" type="number" name="monitor_save_day" value="'+info.monitor_save_date+'" style="width:310px" placeholder="Monitoring Save days">\
                        <button class="btn btn-success btn-sm mr10 monitorSubmit">Save</button>\
                        <span class="unit">* Set the container page monitoring savory days</span>\
                    </div>\
                </div>\
                <div class="line">\
                    <span class="tname">Registry mirrors: </span>\
                    <div class="info-r">\
                        <input class="bt-input-text" readonly disabled value="'+info.registry_mirrors+'" style="width:310px" placeholder="Unprocessed acceleration URL">\
                        <button class="btn btn-success btn-sm editSpeed">Modify</button>\
                    </div>\
                </div>\
            </div>'
            $('#dk_setup_form').html(_html)
            $('#monitor_status').prop('checked',info.monitor_status)  //监控状态
            //服务按钮
            $('.serveSetup').click(function(){
                var _set = $(this).data('setup');
                that.ajax_task_method('docker_service',{data:{act:_set},tips:'Set the docker service status'},function(ress){
                    if(ress.status) that.initTabConfig('setup')
                    bt_tools.msg(ress)
                })
            })
            //容器监控开关
            $("#monitor_status").change(function(){
                var _status = $(this).prop('checked');
                that.ajax_task_method('set_docker_monitor',{data:{act:_status?'start':'stop'},tips:'Set container monitoring configuration'},function(res){
                    if(res.status) that.initTabConfig('setup')
                    bt_tools.msg(res)
                })
            })
            //容器监控天数
            $('.monitorSubmit').click(function(){
                var save_num = $('[name=monitor_save_day]').val();
                if(save_num <= 0)return layer.msg('The number of monitoring and preservation cannot be less than 0',{icon:2})

                that.ajax_task_method('set_monitor_save_date',{data:{save_date:save_num},tips:'Set container monitoring configuration'},function(res){
                    if(res.status) that.initTabConfig('setup')
                    bt_tools.msg(res)
                })
            })
            //设置加速url
            $('.editSpeed').click(function(){
                bt_tools.open({
                    title:'Set the acceleration URL',
                    type:1,
                    shadeClose: false,
                    closeBtn: 2,
                    area:'520px',
                    content:{
                        'class':'pd20',
                        form:[{
                            label:'Accelerate URL',
                            group:{
                                type:'text',
                                name:'registry_mirrors_address',
                                value:info.registry_mirrors,
                                width:'360px',
                                placeholder:'Please enter the acceleration URL'
                            }
                        },{
                            label:'',
                            group:{
                                type:'help',
                                style:{'margin-top':'0'},
                                list:[
                                    'Priority use the acceleration URL to perform operations, and the request timeout will skip the use of the default acceleration method',
                                    'After setting acceleration, you need to restart the docker manually',
                                    'Turn off acceleration, please set it to empty'
                                ]
                            }
                        }]
                    },yes:function(formD,index){
                        that.ajax_task_method('set_registry_mirrors',{data:formD,tips:false},function(uRes){
                            if(uRes.status){
                                layer.close(index)
                                that.initTabConfig('setup')
                            } 
                            bt_tools.msg(uRes)
                        })
                    }
                })
            })
        })
        
        
    },
    /**
     * @description 添加容器
     */
    add_container:function(){
			var that = this, _imageList = '', _volumesList = '', add_pro = null;
			if (this.dk_images.length > 0) {
				$.each(this.dk_images, function (index, item) {
					_imageList += '<option value="' + item.name + '">' + item.name + '</option>'
				})
			}
			if (this.dk_volumes.length > 0) {
				$.each(this.dk_volumes, function (index, item) {
					_volumesList +='<li data-key="' + item.Name + '" title="' + item.Name + '">' + item.Name + '</li>'
				})
			}
			
			layer.open({
				type: 1,
				closeBtn: 2,
				title: lan.docker.container.add_container,
				area: ['720px','630px'],
				skin: 'add_container',
				btn: [lan.public.submit, lan.site.no],
				shadeClose: false,
				content: '\
				<div class="pd20">\
					<div class="tab-nav mb15">\
						<span class="on">' + lan.docker.container.create_container + '</span>\
						<span>' + lan.docker.container.container_arr + '</span>\
					</div>\
					<div class="tabs_content">\
						<div class="tabpanel">\
							<div class="bt-form" style="height: 450px;overflow: overlay;">\
								<div class="line"><span class="tname">' + lan.docker.public.container + '</span>\
									<div class="info-r">\
										<input class="bt-input-text" name="dk_container_name" style="width: 200px" placeholder="' + lan.docker.container.container_input_tips + '">\
										<span class="line-tname">' + lan.docker.container.mirror_image + '</span>\
										<select class="bt-input-text" name="dk_image" style="width: 160px">'+_imageList+'</select>\
									</div>\
								</div>\
								<div class="line">\
									<span class="tname">' + lan.public.port + '</span>\
									<div class="info-r">\
										<select class="bt-input-text" name="dk_port" style="width: 200px">\
											<option value="0">' + lan.docker.container.port_select1 + '</option>\
											<option value="1">' + lan.docker.container.port_select2 + '</option>\
										</select>\
										<div class="mt10 dk_port_setting">\
											<input class="bt-input-text" name="dk_port_map" style="width:200px" placeholder="' + lan.docker.container.container_port + '">\
											<span class="minus">-</span>\
											<input class="bt-input-text" name="dk_server_map" style="width:200px" placeholder="' + lan.docker.container.server_port + '">\
											<span class="plus" data-type="port">+</span>\
											<div class="divtable dk_port_table mt10">\
												<table class="table table-hover">\
													<thead>\
														<tr>\
															<th>' + lan.docker.container.container_port + '</th>\
															<th>' + lan.docker.container.server_port + '</th>\
															<th width="70" class="text-right">' + lan.public.operate + '</th>\
														</tr>\
													</thead>\
													<tbody>\
														<tr><td colspan="3" class="text-center">' + lan.site.data_empty + '</td></tr>\
													</tbody>\
												</table>\
											</div>\
										</div>\
									</div>\
								</div>\
								<div class="line">\
									<span class="tname">' + lan.docker.container.boot_command + '</span>\
									<div class="info-r">\
										<input class="bt-input-text" name="dk_start_cmd" style="width:482px" placeholder="' + lan.docker.container.boot_command_input_tips + '">\
									</div>\
								</div>\
								<div class="line">\
									<span class="tname"></span>\
									<div class="info-r" style="min-height: auto; height: auto; line-height: 1.4;">\
										<span class="shop_container_del cu-pointer">\
											<i class="cust—checkbox form-checkbox" style="position: relative; top: -2px; margin-right: 5px;"></i>\
											<span>' + lan.docker.container.shop_container_del + '</span>\
											<input type="checkbox" class="hide">\
										</span>\
									</div>\
								</div>\
								<div class="line">\
									<span class="tname">' + lan.docker.container.limit_cpu + '</span>\
									<div class="info-r">\
										<input class="bt-input-text" value="1.0" type="number" name="dk_cpu_num" style="width:200px;border-top-right-radius: 0;border-bottom-right-radius: 0;">\
										<span class="line-tname">' + lan.index.process_mem + '</span>\
										<input class="bt-input-text" value="100" type="number" name="dk_cpu_size" style="width:124px">\
										<select class="bt-input-text" name="dk_cpu_unit" style="width:60px">\
											<option value="k">KB</option>\
											<option value="MB" selected>MB</option>\
											<option value="g">GB</option>\
										</select>\
									</div>\
								</div>\
								<div class="line">\
									<span class="tname">' + lan.docker.container.mount_volume + '</span>\
									<div class="info-r">\
										<div class="">\
											<div class="dk_volumes_box">\
												<input class="bt-input-text" name="dk_server_path" style="width: 175px" placeholder="' + lan.docker.container.server_directory + '">\
												<ul class="dk_volumes">' + _volumesList + '</ul>\
												<select class="bt-input-text" name="volumes_type" style="width: 100px">\
													<option value="rw">' + lan.index.process_disk + '</option>\
													<option value="ro">' + lan.docker.container.read_only + '</option>\
												</select>\
												<input class="bt-input-text" name="dk_volumes_path" style="width:170px" placeholder="' + lan.docker.container.container_directory + '">\
												<span class="plus" data-type="path">+</span>\
												<div class="divtable dk_path_table mt10">\
													<table class="table table-hover">\
														<thead>\
															<tr>\
																<th>' + lan.docker.container.server_directory + '</th>\
																<th>' + lan.public.permission + '</th>\
																<th>' + lan.docker.container.container_directory + '</th>\
																<th width="70" class="text-right">' + lan.public.operate + '</th>\
															</tr>\
														</thead>\
														<tbody>\
															<tr><td colspan="4" class="text-center">' + lan.site.data_empty + '</td></tr>\
														</tbody>\
													</table>\
												</div>\
											</div>\
										</div>\
									</div>\
								</div>\
								<div class="line">\
									<span class="tname">' + lan.docker.container.tag + '</span>\
									<div class="info-r">\
										<textarea placeholder="' + lan.docker.container.tag_textarea_tips + '" name="dk_tag" class="bt-input-text" style="width: 482px; height: 80px; resize: auto; line-height: 20px;"></textarea>\
									</div>\
								</div>\
								<div class="line">\
									<span class="tname" style="height: auto;line-height: 20px;">' + lan.docker.container.env_variable + '</br>' + lan.docker.container.one_line + '</span>\
									<div class="info-r">\
										<textarea placeholder="' + lan.docker.container.env_variable_textarea_tips + 'java_home =/usr/local/java8&#10;HOSTNAME=master" class="bt-input-text" name="dk_config" style="width: 482px; height: 80px; resize: auto; line-height: 20px;"></textarea>\
									</div>\
								</div>\
								<div class="line">\
									<span class="tname">' + lan.docker.container.restart_rule + '</span>\
									<div class="info-r">\
										<select class="bt-input-text" name="dk_reset" style="width:200px">\
											<option value="always">' + lan.docker.container.restart_rule_select1 + '</option>\
											<option value="on-failure">' + lan.docker.container.restart_rule_select2 + '</option>\
											<option value="" selected>' + lan.docker.container.restart_rule_select3 + '</option>\
										</select>\
										<span class="c9 ml5">*' + lan.docker.container.restart_rule_select_tips + '</span>\
									</div>\
								</div>\
							</div>\
						</div>\
						<div class="tabpanel" style="display:none;">\
							<div id="add_project_form"></div>\
						</div>\
					</div>\
				</div>',
				success:function(){
					$(".add_container").on('click', '.tab-nav span', function () {
						var index = $(this).index();
						$(this).addClass('on').siblings().removeClass('on');
						$('.tabs_content .tabpanel').eq(index).removeAttr('style').siblings().attr('style','display:none')
					});
					// <----------容器----------->
					//服务器目录事件
					$('[name=dk_server_path]').click(function(e){
						var _ul = $(this).siblings('ul')
						if (_ul.hasClass('show')) {
							_ul.removeClass('show')
						} else {
							_ul.addClass('show')
						}
						$(document).one('click',function(){
							_ul.removeClass('show');
						})
						e.stopPropagation();
					})
					// 服务器目录ul
					$('.dk_volumes li').click(function(){
						$('[name=dk_server_path]').val($(this).data('key'))
					})
					// 端口类型触发
					$('[name=dk_port]').change(function(){
						$(this).val() == 1 ? $('.dk_port_setting').hide() : $('.dk_port_setting').show();
					})
					//添加端口、目录tbody
					$('.plus').click(function(){
						var _Arrinput = $(this).siblings('input'),
								_val_one = $(_Arrinput[0]).val(),
								_val_two = $(_Arrinput[1]).val(),
								THbody = $(this).siblings('.divtable').find('tbody'),
								_td = '';
						
						if (_val_one == '') return layer.msg(lan.docker.public.please_enter + $(_Arrinput[0]).attr('placeholder'),{icon:2})
						if (_val_two == '') return layer.msg(lan.docker.public.please_enter + $(_Arrinput[1]).attr('placeholder'),{icon:2})

						switch($(this).data('type')){
							case 'port':
								_td = '\
								<tr>\
									<td>' + _val_one + '</td>\
									<td>' + _val_two + '</td>\
									<td><a class="btlink pull-right del-change-td">' + lan.public.del + '</a></td>\
								</tr>'
								break;
							case 'path':
								var pess_type = $('[name=volumes_type]').val();
								_td = '\
								<tr>\
									<td>\
										<span style="display: flex;">\
											<span class="size_ellipsis" style="flex: 1; width: 0;" title="' + _val_one + '">' + _val_one + '</span>\
										</span>\
									</td>\
									<td>' + pess_type + '</td>\
									<td>\
										<span style="display: flex;">\
											<span class="size_ellipsis" style="flex: 1; width: 0;" title="'+_val_two+'">'+_val_two+'</span>\
										</span>\
									</td>\
									<td><a class="btlink pull-right del-change-td">' + lan.public.del + '</a></td>\
								</tr>'
								break;
						}
						
						if (THbody.find('td').length === 1) {
							$(THbody).html(_td)
						} else {
							$(THbody).append(_td)
						}

						//清空输入框内容
						$(_Arrinput[0]).val('')
						$(_Arrinput[1]).val('')
					})
					// 端口、目录删除
					$('.add_container').on('click','.del-change-td',function(){
						var tbody = $(this).parents('tbody')
						$(this).parents('tr').remove()
						if (tbody.find('tr').length == 0) {
							tbody.append('<tr><td colspan="4" class="text-center">' + lan.site.data_empty + '</td></tr>');
						}
					})
					// 停止后自动删除容器事件
					$('.add_container .shop_container_del').click(function(){
						if ($(this).find('i').hasClass('active')) {
							$(this).find('i').removeClass('active').siblings('input').prop('checked',false)
						} else {
							$(this).find('i').addClass('active').siblings('input').prop('checked',true)
						}
					});

					// <-----------------容器编排------------------->
					var modelList = []
					render_model_list()
					add_pro = bt_tools.form({
						el:'#add_project_form',
						form: [
							{
								label: lan.docker.public.compose_template,
								group:[
									{
										type: 'select',
										name: 'template_id',
										width: '440px',
										list: modelList
									},
									{
										type: 'link',
										title: lan.public_backup.create,
										event: function () {
											that.add_model_view(function(resolve){
												if(resolve){
													that.ajax_task_method('template_list', {
														tips: lan.docker.compose_template.getting_template,
														model_name: { dk_model_name: 'compose' }
													}, function (model_list) {
														that.dk_template = model_list['msg']['template']
														render_model_list()
														add_pro['config']['form'][0]['group'][0]['list'] = modelList;  // 模板列表
														add_pro.$local_refresh("template_id", add_pro['config']['form'][0]['group'][0])  // 刷新局部数据
													})
												}
											})
										}
									}
								]
							},
							{
								label: lan.public.name,
								group: {
									type: 'text',
									name: 'project_name',
									width: '440px',
									placeholder: lan.docker.compose.name_input_tips
								}
							},
							{
								label: lan.one_click.description,
								group: {
									type: 'textarea',
									name: 'remark',
									style: {
										'width': '440px',
										'min-width': '380px',
										'min-height': '130px',
										'line-height': '22px',
										'padding-top': '5px',
										'resize': 'both'
									},
									placeholder: lan.docker.compose.description_input_tips
								}
							}
						]
					})
					function render_model_list () {
						if (that.dk_template.length > 0) {
							$.each(that.dk_template,function(index,item){
								modelList.push({title:item.name,value:item.id})
							})
						} else {
							modelList = [
								{ value:'dk_project_false', title: lan.docker.compose.compose_template_select_tips }
							]
						}
					}
				},
				yes: function (indexs) {
					// 创建容器
					if ($('.add_container .tab-nav span.on').index() == 0) {
						var _name = $('[name=dk_container_name]').val(),
								_image = $('[name=dk_image]').val(),
								_port = $('[name=dk_port]').val(),
								_start_cmd = $('[name=dk_start_cmd]').val(),
								auto_remove = $('.form-checkbox').siblings('input').prop('checked')?1:0,
								_cpus = $('[name=dk_cpu_num]').val(),
								_size = $('[name=dk_cpu_size]').val(),
								_unit = $('[name=dk_cpu_unit]').val(),
								_tag = $('[name=dk_tag]').val(),
								_config = $('[name=dk_config]').val(),
								_reset = $('[name=dk_reset]').val();
									
							// 验证
							if (_name == '') return layer.msg(lan.docker.container.add_container_tips1, { icon: 2 });
							if (_image == '') return layer.msg(lan.docker.container.add_container_tips2, { icon: 2 });
							if (_cpus != '' && _cpus <= 0)return layer.msg(lan.docker.container.add_container_tips3, { icon: 2 })
							if (_size != '' && _size <= 0)return layer.msg(lan.docker.container.add_container_tips4, { icon: 2 })

							var _form = {
									name: _name,
									image:_image,
									publish_all_ports:_port,
									command:_start_cmd,
									auto_remove:auto_remove,
									environment:_config,
									cpuset_cpus:_cpus,
									mem_limit:_size+_unit,
									labels:_tag,
									restart_policy:{Name:_reset,MaximumRetryCount:5}
							}
							var port_array = {},path_array = {}
							// 端口
							if ($('.dk_port_table tbody tr').length > 0) {
								$.each($('.dk_port_table tbody tr'), function(index, item) {
									if ($(item).find('td').length == 3) {
										port_array[$(item).find('td').eq(0).text()+'/tcp'] = $(item).find('td').eq(1).text();
									}
								});
								_form['ports'] = port_array;
							}
							// 路径
							if ($('.dk_path_table tbody tr').length > 0) {
								$.each($('.dk_path_table tbody tr'),function(index,item){
									if ($(item).find('td').length == 4) {
										path_array[$(item).find('td').eq(0).find('.size_ellipsis').text()] = {
											bind: $(item).find('td').eq(2).find('.size_ellipsis').text(),
											mode: $(item).find('td').eq(1).text()
										}
									}
								})
								_form['volumes'] = path_array
							}
							//接口参数
							that.ajax_task_method('run', {
								data: $.extend(_form,that.global),
								tips: lan.docker.container.add_container_api_tips
							}, function (res) {
								if (res.status) {
									layer.close(indexs);
									that.initTabConfig('container');  // 刷新列表
								}
								bt_tools.msg(res);
							})
					} else {
						var formValue = add_pro.$get_form_value()
						if (formValue.template_id === 'dk_project_false') return bt_tools.msg(lan.docker.compose.add_compose_tips1, 2)
						if (formValue.project_name == '') return layer.msg(lan.docker.compose.add_compose_tips2, { icon: 2 })
						
						that.get_log_situation();
						that.ajax_task_method('create', {
							data: formValue,
							tips: false,
							model_name: { dk_model_name: 'compose' }
						}, function (res) {
							that.remove_log_clearinterval();
							if (res.status) {
								layer.closeAll();
								$('#cutMode .tabs-item').eq(2).click() // 跳转到容器编排
							} 
							bt_tools.msg(res)
						});
					}
				}
			})
    },
    /**
     * @description 添加Compose
     */
    add_project:function(){
        var that = this,add_pro = null
        bt_tools.open({
            title: lan.docker.compose.add_btn,
            btn: [lan.public.submit, lan.site.no],
            area: ['560px', '380px'],
            content: '<div class="pd20 add_project_form" id="add_project_form"></div>',
            success: function () {
                var modelList = []
                render_model_list()
                add_pro = bt_tools.form({
                    el:'#add_project_form',
                    form: [{
											label: lan.docker.public.compose_template,
											group:[
												{
													type: 'select',
													name:'template_id',
													width:'300px',
													list:modelList
                        },
												{
													type:'link',
													title: lan.public_backup.create,
													event:function(){
														that.add_model_view(function(resolve){
															if (resolve) {
																that.ajax_task_method('template_list', {
																	tips: lan.docker.compose_template.getting_template,
																	model_name: {
																		dk_model_name: 'compose'
																	}
																}, function (model_list) {
																	that.dk_template = model_list['msg']['template']
																	render_model_list()
																	add_pro['config']['form'][0]['group'][0]['list'] = modelList;  // 模板列表
																	add_pro.$local_refresh("template_id", add_pro['config']['form'][0]['group'][0])  // 刷新局部数据
																})
															}
														})
													}
                        }
											]
                    },{
                        label: lan.public.name,
                        group: {
													type: 'text',
													name: 'project_name',
													width: '300px',
													placeholder: lan.docker.compose.name_input_tips
                        }
                    },{
                        label: lan.one_click.description,
                        group: {
                          type: 'textarea',
                          name: 'remark',
                          style: {
                            'width': '300px',
                            'min-width': '300px',
                            'min-height': '130px',
                            'line-height': '22px',
                            'padding-top': '5px',
                            'resize': 'both'
                          },
                          placeholder: lan.docker.compose.description_input_tips
                        }
                    }]
                })
                function render_model_list () {
									if (that.dk_template.length > 0) {
										$.each(that.dk_template, function(index, item) {
											modelList.push({ title: item.name, value: item.id });
										});
									}else{
										modelList = [
											{ value:'dk_project_false', title: lan.docker.compose.compose_template_select_tips }
										]
									}
                }
            },
            yes:function(indexs){
                var formValue = add_pro.$get_form_value()
                if (formValue.template_id === 'dk_project_false') return bt_tools.msg(lan.docker.compose.add_compose_tips1, 2)
                if(formValue.project_name == '')return layer.msg(lan.docker.compose.add_compose_tips2,{icon:2})
                that.get_log_situation()
                that.ajax_task_method('create',{data:formValue,tips:false},function(res){
                    that.remove_log_clearinterval();
                    if(res.status){
                        layer.closeAll();
                        that.initTabConfig('compose')  //刷新列表
                    } 
                    bt_tools.msg(res)
                })
            }
        })
    },
    /**
     * @description 添加Compose模板
     */
    add_model_view:function(callback){
        var that = this,loca_compose = null,search_list = []
        var model_tabl = bt_tools.tab({
            class:'pd20',
            type:0,
            active:1,
            theme: { nav: 'yaml' },
            list:[{
                title: lan.docker.compose_template.add_title,
                name:"addCompose",
                content: '<div class="bt-form">\
                    <div class="line">\
											<span class="tname">' + lan.docker.compose_template.create_template + '</span>\
											<div class="info-r">\
													<input class="bt-input-text" name="model_name" style="width:350px" placeholder="' + lan.docker.compose_template.create_template_input + '">\
											</div>\
                    </div>\
                    <div class="line">\
											<span class="tname">' + lan.one_click.remark + '</span>\
											<div class="info-r">\
												<input class="bt-input-text" name="model_desc" style="width:350px" placeholder="' + lan.one_click.remark + '">\
											</div>\
                    </div>\
                    <div class="line">\
											<span class="tname">' + lan.docker.compose_template.content + '</span>\
											<div class="info-r">\
												<div class="bt-input-text" style="width:470px;height: 350px;min-height:300px;line-height:18px;" id="dkContntBody"></div>\
											</div>\
                    </div>\
                </div>',
                success:function(){
                    _aceEditor = bt.aceEditor({ el: 'dkContntBody', content: '' });
                }
            },{
                title: lan.docker.compose_template.search_local_template,
                name:'searchCompose',
                content:'\
								<div class="bt-form ptb15 loca_compose_box">\
									<div class="model_sc_top">\
										<input class="bt-input-text" style="width:515px;padding-right: 95px;" id="model_sc_path" placeholder="' + lan.docker.compose_template.search_input_tips + '">\
										<div class="model_sc_child">\
											<i class="cust—checkbox form-checkbox"></i>\
											<input type="checkbox" class="hide">\
										</div>\
										<i class="glyphicon glyphicon-folder-open ml5 mr20 cu-pointer" onclick="bt.select_path(\'model_sc_path\',\'dir\')"></i>\
										<button type="button" class="btn btn-success btn-sm model_search_btn">' + lan.docker.compose_template.search + '</button>\
									</div>\
									<div id="model_sc_table"></div>\
                </div>',
                success:function(){
                    var one = 0;
                    loca_compose = bt_tools.table({
                        el:'#model_sc_table',
                        data:search_list,
                        height: '330px',
                        column:[{
                            type: 'checkbox', 
                            class: '', 
                            width: 20 
                        },{
                            width:180,
                            title: lan.docker.compose_template.compose_template_name,
                            template:function(row){
                                return '<span class="size_ellipsis" style="width:164px" title="'+row.project_name+'">'+row.project_name+'</span>'
                            }
                        },{
                            width:180,
                            title: lan.docker.container.path,
                            template:function(row){
                                return '<span class="size_ellipsis" style="width:164px" title="'+row.conf_file+'">'+row.conf_file+'</span>'
                            }
                        },{
                            fid: 'remark',
                            title: lan.one_click.description,
                            type: 'input',
                            blur: function (row, index, ev, key, thatc) {
                                row.remark = ev.target.value
                            },
                            keyup: function (row, index, ev) {
                              if (ev.keyCode === 13) {
                                $(this).blur();
                              }
                            }
                        }],
                        success:function(){
													if(one == 0){
														one++
														$('#model_sc_table').on('click', '.cust—checkbox', function (e) {
																var len = loca_compose.checkbox_list
																$('.lc_select').html(len.length+'个')
														})
														$('.loca_compose_box').append('\
														<ul class="help-info-text red">\
															<li>' + lan.docker.compose_template.add_search_tips1 + ' [' + lan.docker.compose_template.selected + ': <span class="lc_select">0</span>]</li>\
														</ul>');
													}
                        }
                    })
                    //停止后自动删除容器事件
                    $('.model_sc_child').click(function(){
                        if($(this).find('i').hasClass('active')){
                            $(this).find('i').removeClass('active').siblings('input').prop('checked',false)
                        }else{
                            $(this).find('i').addClass('active').siblings('input').prop('checked',true)
                        }
                    })
                    // 模板搜索按钮
                    $('.model_search_btn').click(function(){
											var _val = $('#model_sc_path').val(),
													_child = $('.form-checkbox').siblings('input').prop('checked')?1:0
											if(_val == '') return bt_tools.msg(lan.docker.compose_template.search_folder_tips1, 2)
											that.ajax_task_method('get_compose_project',{
												data: { path: _val, sub_dir: _child },
												tips: lan.docker.compose.getting_compose,
												model_name:{ dk_model_name: 'compose' }
											}, function (mlist) {
												if(mlist.status == false)return bt_tools.msg(mlist.msg,2)
												if(mlist.length == 0)return bt_tools.msg(lan.docker.compose_template.search_folder_tips2, 0)
												loca_compose.$reader_content(mlist)
											})
                    })
                }
            }]
        })

        bt_tools.open({
            title: lan.docker.compose_template.add_yaml_template,
            btn: [lan.public.submit, lan.site.no],
            skin:'model_sc_view',
						area: ['680px', '640px'],
            content:model_tabl.$reader_content(),
            success:function(){
                model_tabl.$init();
            },
            yes:function(layers){
                if (model_tabl.active == 0) {
                    var _mName = $('[name=model_name]').val(),
												_mDesc = $('[name=model_desc]').val(),
												_Con = _aceEditor.ACE.getValue(); 
                    
									if (_mName == '') return layer.msg(lan.docker.compose_template.add_template_tips1,{icon:2})
									if (_Con == '') return layer.msg(lan.docker.compose_template.add_template_tips2,{icon:2})
									
									var _param = {name:_mName,remark:_mDesc,data:_Con}
									that.ajax_task_method('add_template', {
										data: _param,
										tips: lan.docker.compose_template.adding_template,
										model_name: { dk_model_name: 'compose' }
									}, function (res) {
										if (res.status) {
											layer.close(layers)
											if (callback) {
												callback(res.status)
											} else {
												that.initTabConfig('model')  //刷新列表
											}
										} 
										var entry = { "'": "&apos;", '"': '&quot;', '<': '&lt;', '>': '&gt;' };
									 	res.msg = res.msg.replace(/(['")-><&\\\/\.])/g, function ($0) { return entry[$0] || $0; });
										bt_tools.msg(res)
									})
                } else {
									var check_len = loca_compose.checkbox_list.length,
											array = []
									$.each(loca_compose.data,function(index,item){
										if ($.inArray(index,loca_compose.checkbox_list) != -1) {
											array.push(item);
										}
									})
									if(check_len == 0) return layer.msg(lan.docker.compose_template.add_path_tips1,{icon:2})

									layer.confirm(lan.docker.compose_template.add_path_tips2 + check_len + lan.docker.compose_template.add_path_tips3, {
										title: lan.docker.compose_template.add_template,
										icon: 3,
										closeBtn: 2
									}, function () {
										that.ajax_task_method('add_template_in_path',{
											data: { template_list: array },
											tips: lan.docker.compose_template.adding_template,
											model_name: { dk_model_name: 'compose' }
										}, function (res) {
											if(res.status){
												layer.close(layers)
												if (callback) {
													callback(res.status)
												}else{
													that.initTabConfig('model')  // 刷新列表
												}
											} 
											bt_tools.msg(res)
										})
									});
                }
            }
        })
    },
    /**
     * @description 模板添加、编辑界面
     * @param {Object} edit 编辑数据
     * @param callback 成功后回调
     */
    edit_model_view:function(edit){
        var that = this,_aceEditor = null;
        layer.open({
            type: 1,
            title: 'Edit template',
            btn: [lan.public.save, lan.site.no],
            area:'650px',
            shadeClose: false,
            closeBtn: 2,
            content: '<div class="pd20 bt-form">\
                <div class="line"><span class="tname">' + lan.docker.compose_template.template_name + '</span>\
                    <div class="info-r">\
                        <input class="bt-input-text" name="model_name" style="width:350px" placeholder="' + lan.docker.compose_template.create_template_input + '" value="'+edit.name+'">\
                    </div>\
                </div>\
                <div class="line"><span class="tname">' + lan.one_click.description + '</span>\
                    <div class="info-r">\
                        <input class="bt-input-text" name="model_desc" style="width:350px" placeholder="' + lan.one_click.description + '" value="'+edit.remark+'">\
                    </div>\
                </div>\
                <div class="line"><span class="tname">' + lan.docker.compose_template.content + '</span>\
                    <div class="info-r">\
                        <div class="bt-input-text" style="width:470px;height: 350px;min-height:300px;line-height:18px;" id="dkContntBody"></div>\
                    </div>\
                </div>\
            </div>',
            success:function(){
                _aceEditor = bt.aceEditor({ el: 'dkContntBody', content: edit.content });
            },
            yes:function(layers){
                var _mName = $('[name=model_name]').val(),
                    _mDesc = $('[name=model_desc]').val(),
                    _Con = _aceEditor.ACE.getValue(); 
                    
                if(_mName == '') return layer.msg(lan.docker.compose_template.add_template_tips1,{icon:2})
                if(_mDesc == '') return layer.msg(lan.docker.compose.description_input_tips,{icon:2})
                if(_Con == '') return layer.msg(lan.docker.compose_template.add_template_tips2,{icon:2})
                
                var _param = {name:_mName,remark:_mDesc,data:_Con}
                if(edit) _param['id'] = edit.id
                that.ajax_task_method('edit_template',{data:_param,tips: lan.docker.compose_template.saving,model_name:{dk_model_name:'compose'}},function(res){
                   if(res.status){
                       layer.close(layers)
                       that.initTabConfig('model')  //刷新列表
                   } 
                   bt_tools.msg(res)
                })
            }
        })
    },
    /**
     * @description 添加网络
     */
    add_network:function(){
        var that = this,add_network = null
        bt_tools.open({
            title: lan.docker.network.add,
            btn: [lan.public.submit, lan.site.no],
            area: ['540px','510px'],
            content: '<div class="ptb20" id="add_network_form"></div>',
            success: function (layers) {
                add_network = bt_tools.form({
                    el:'#add_network_form',
                    form: [{
                        label: lan.docker.network.name,
                        group: {
                            type: 'text',
                            name: 'name',
                            width: '384px',
                            placeholder: lan.docker.network.name_input
                        }
                    },{
                        label: lan.docker.network.device,
                        group:{
                            type: 'select',
                            name:'driver',
                            width:'160px',
                            list:[
                                {title:'bridge',value:'bridge'},
                                {title:'ipvlan',value:'ipvlan'},
                                {title:'macvlan',value:'macvlan'},
                                {title:'overlay',value:'overlay'}
                            ]
                        }
                    },{
                        label: lan.docker.network.parameter,
                        group: {
                          type: 'textarea',
                          name: 'options',
                          style: {
                            'width': '384px',
                            'min-width': '384px',
                            'min-height': '70px',
                            'line-height': '22px',
                            'padding-top': '5px',
                            'resize': 'both'
                          },
                          placeholder: lan.docker.network.parameter_textarea
                        }
                    },{
                        label: lan.docker.network.sub_network,
                        group:[{
                            type: 'text',
                            name: 'subnet',
                            width: '160px',
                            placeholder: lan.docker.network.sub_network_input
                        },{
                            label: lan.docker.network.gateway,
                            type: 'text',
                            name: 'gateway',
                            width: '160px',
                            placeholder: lan.docker.network.gateway_input
                        }]
                    },{
                        label: lan.docker.network.ip_range,
                        group: {
                            type: 'text',
                            name: 'iprange',
                            width: '384px',
                            placeholder: lan.docker.network.ip_range_input
                        }
                    },{
                        label: lan.docker.container.tag,
                        group: {
                          type: 'textarea',
                          name: 'labels',
                          style: {
                            'width': '384px',
                            'min-width': '384px',
                            'min-height': '70px',
                            'line-height': '22px',
                            'padding-top': '5px',
                            'resize': 'both'
                          },
                          placeholder: lan.docker.network.tag_textarea
                        }
                    }]
                })
            },
            yes:function(layers){
                var formValue = add_network.$get_form_value()
                if(formValue.name == '')return layer.msg(lan.docker.network.add_tips1,{icon:2})
                if(formValue.options == '')return layer.msg(lan.docker.network.add_tips2,{icon:2})
                if(formValue.subnet == '')return layer.msg(lan.docker.network.add_tips3,{icon:2})
                if(formValue.gateway == '')return layer.msg(lan.docker.network.add_tips4,{icon:2})
                if(formValue.iprange == '')return layer.msg(lan.docker.network.add_tips5,{icon:2})

                that.ajax_task_method('add',{data:formValue,tips:lan.docker.network.adding},function(res){
                    if(res.status){
                        layer.close(layers)
                        that.initTabConfig('network')  //刷新列表
                    } 
                    bt_tools.msg(res)
                })
            }
        })
    },
    /**
    * @description 添加存储卷
    */
    add_volume:function(){
        var that = this,add_volume = null
        bt_tools.open({
            title: lan.docker.volume.add,
            btn: [lan.public.submit, lan.site.no],
            area:['540px','420px'],
            content: '<div class="ptb20" id="add_volume_form"></div>',
            success: function (layers) {
                add_volume = bt_tools.form({
                    el:'#add_volume_form',
                    form: [{
                        label: lan.docker.public.volume,
                        group: {
                            type: 'text',
                            name: 'name',
                            width: '358px',
                            placeholder: lan.docker.volume.name_input
                        }
                    },{
                        label: lan.docker.volume.driver,
                        group:{
                            type: 'select',
                            name:'driver',
                            width:'160px',
                            list:[
                                {title:'local',value:'local'}
                            ]
                        }
                    },{
                        label: lan.docker.volume.option,
                        group: {
                          type: 'textarea',
                          name: 'driver_opts',
                          style: {
                            'width': '358px',
                            'min-width': '358px',
                            'min-height': '70px',
                            'line-height': '22px',
                            'padding-top': '5px',
                            'resize': 'both'
                          },
                          placeholder: lan.docker.volume.option
                        }
                    },{
                        label: lan.docker.public.tag,
                        group: {
                          type: 'textarea',
                          name: 'labels',
                          style: {
                            'width': '358px',
                            'min-width': '358px',
                            'min-height': '70px',
                            'line-height': '22px',
                            'padding-top': '5px',
                            'resize': 'both'
                          },
                          placeholder: lan.docker.volume.tag_textarea
                        }
                    }]
                })
            },
            yes:function(indexs){
                var formValue = add_volume.$get_form_value()
                if(formValue.name == '')return layer.msg(lan.docker.volume.add_tips1,{icon:2})

                that.ajax_task_method('add',{data:formValue,tips:lan.docker.volume.adding},function(res){
                    if(res.status){
                        layer.close(indexs);
                        that.initTabConfig('volume')  //刷新列表
                    }
                    bt_tools.msg(res)
                })
            }
        })
    },
    /**
    * @description 仓库添加、编辑界面
    * @param {Object} edit 编辑数据
    */
    render_registry_view:function(edit){
        var that = this,add_registry = null,is_edit = false
        if(edit){
            edit['registry'] = edit['url']
            is_edit = true
        }
        bt_tools.open({
            title: (is_edit ? lan.public.edit : lan.public.add) + ' ' + lan.docker.public.repository.toLowerCase(),
            btn: [is_edit ? lan.site.save: lan.public.submit, lan.site.no],
            area:['580px','420px'],
            content: '<div class="ptb20 add_registry_form" id="add_registry_form"></div>',
            success: function (layers) {
                add_registry = bt_tools.form({
                    el:'#add_registry_form',
                    form: [{
                        label: lan.docker.repository.address,
                        group: {
                            type: 'text',
                            name: 'registry',
                            width: '340px',
                            placeholder: lan.docker.repository.address_input
                        }
                    },{
                        label: lan.docker.repository.name,
                        group: {
                            type: 'text',
                            name: 'name',
                            width: '340px',
                            placeholder: lan.docker.repository.name_input
                        }
                    },{
                        label: lan.docker.repository.username,
                        group:[{
                            type: 'text',
                            name: 'username',
                            width: '340px',
                            placeholder: lan.docker.repository.user_input
                        }]
                    },
										{
											label: lan.docker.repository.pwd,
											group: [
												{
													type: 'text',
													name: 'password',
													width: '340px',
													placeholder: lan.docker.repository.pwd_input
												}
											]
										},
										{
                        label: lan.docker.repository.namespaces,
                        group: [{
                            type: 'text',
                            name: 'namespace',
                            width: '340px',
                            placeholder: lan.docker.repository.namespaces_input
                        },{
                            type:'link',
                            title: '?',
                            class:'bt-ico-ask',
                            event:function(){
                                window.open('https://www.bt.cn/bbs/thread-80965-1-1.html')
                            }
                        }]
                    },{
                        label: lan.one_click.description,
                        group: {
                            type: 'text',
                            name: 'remark',
                            width: '340px',
                            placeholder: lan.docker.compose.description_input_tips
                        }
                    }],
                    data:edit?edit:{}
                })
            },
            yes:function(indexs){
                var formValue = add_registry.$get_form_value()
                if(formValue.registry == '')return layer.msg(lan.docker.repository.form_tips1,{icon:2})
                if(formValue.name == '')return layer.msg(lan.docker.repository.form_tips2,{icon:2})
                if(formValue.username == '')return layer.msg(lan.docker.repository.form_tips3,{icon:2})
                if(formValue.password == '')return layer.msg(lan.docker.repository.form_tips4,{icon:2})
                if(formValue.namespace == '')return layer.msg(lan.docker.repository.form_tips5,{icon:2})

                if(edit) formValue['id'] = edit['id']
                that.ajax_task_method(is_edit?'edit':'add',{data:formValue,tips:(edit? lan.public.save : lan.public.add) + ' ' + lan.docker.public.repository.toLowerCase()},function(res){
                    if(res.status){
                        layer.close(indexs);
                        that.initTabConfig('registry')  //刷新列表
                    }
                    bt_tools.msg(res)
                })
            }
        })
    },
    /**
    * @description 构建镜像
    */
    construction_image:function(){
        var that = this,_aceEditor = null;
        layer.open({
            type: 1,
            title: lan.docker.image.build_title,
            btn: [lan.public.submit, lan.site.no],
            area:'580px',
            content: '<div class="bt-form pd20 constr_image">\
                <div class="line"><span class="tname">Dockerfile</span>\
                    <div class="info-r">\
                        <select class="bt-input-text" name="dockerfile_type" style="width:100px">\
                            <option value="0">' + lan.site.path + '</option>\
                            <option value="1">' + lan.docker.compose_template.content + '</option>\
                        </select>\
                        <div class="df_type" style="display: inline-block;">\
                            <input class="bt-input-text" name="df_path" style="width:288px" id="df_path" placeholder="' + lan.docker.image.dockerfile_input + '">\
                            <i class="glyphicon glyphicon-folder-open ml5 cu-pointer" onclick="bt.select_path(\'df_path\',\'file\')"></i>\
                        </div>\
                        <div class="df_type" style="display:none">\
                            <div class="bt-input-text" style="margin-top:7px; width:393px;height: 230px;min-height:200px;line-height:18px;" id="dkFileBody"></div>\
                        </div>\
                    </div>\
                </div>\
                <div class="line"><span class="tname">' + lan.docker.container.tag + '</span>\
                    <div class="info-r">\
                        <textarea placeholder="' + lan.docker.container.tag_textarea_tips + '" name="dk_tag" class="bt-input-text" style="width: 393px; height: 70px; resize: auto; line-height: 20px;"></textarea>\
                    </div>\
                </div>\
            </div>',
            success:function(){
                _aceEditor = bt.aceEditor({ el: 'dkFileBody', content:'' });
                $('[name=dockerfile_type]').change(function(){
                    switch($(this).val()){
                        case '0':
                            $('.constr_image .df_type:eq(0)').show();
                            $('.constr_image .df_type:eq(1)').hide();
                            $('[name=df_path]').val('');
                            break;
                        case '1':
                            $('.constr_image .df_type:eq(1)').show();
                            $('.constr_image .df_type:eq(0)').hide();
                            _aceEditor.ACE.setValue('')
                            break;
                    }
                })
            },
            yes:function(layers){
                var _mType = $('[name=dockerfile_type]').val(),
                    _mDesc = $('[name=dk_tag]').val(),
                    _Con = _aceEditor.ACE.getValue(),
                    param = {tag:_mDesc}
                if(_mType == '0'){
                    param['path'] = $('[name=df_path]').val()
                }else{
                    param['data'] = _Con
                }
                that.get_log_situation()
                that.ajax_task_method('build',{data:param,tips:false},function(res){
                    that.remove_log_clearinterval();
                    if(res.status){
                        layer.closeAll()
                        that.initTabConfig('model')  //刷新列表
                    }
                    bt_tools.msg(res)
                })
            }
        })
    },
    /**
    * @description 容器监控【获取并整理实时数据，刷新图表】
    * @param {Object} row 容器信息
    */
    transform_cont_chart_data:function(row){
        var that = this,_time = new Date().getTime();
        this.ajax_task_method('stats',{data:{id:row.id},tips:false,model_name:{dk_model_name:'status'}},function(res){
            var _data = res.msg;
            if(!res.status){
                that.remove_cont_chart_data();
                bt_tools.msg(res);
                return false
            }
            //基础信息
            $('.cont_chart_basis').eq(0).find('span').html(bt.format_size(_data.limit))
            $('.cont_chart_basis').eq(1).find('span').html(lan.index.net_up + ': ' + bt.format_size(_data.tx_total)+' - '+ lan.index.net_down + ': '+bt.format_size(_data.rx_total))
            that.cont_chart.time_list.push(_time)
            that.cont_chart.mem_list['usage'].push([_time, bt.format_size(_data.usage,false,null,'MB')])
            that.cont_chart.mem_list['cache'].push([_time,bt.format_size(_data.cache,false,null,'MB')])
            that.cont_chart.cpu_list.push([_time,_data.cpu_usage])
            that.cont_chart.disk_list['read'].push([_time, bt.format_size(_data.read_total,false,null,'MB')])
            that.cont_chart.disk_list['write'].push([_time, bt.format_size(_data.write_total,false,null,'MB')])
            that.cont_chart.network_list['tx'].push([_time, bt.format_size(_data.tx,false,null,'KB')])
            that.cont_chart.network_list['rx'].push([_time, bt.format_size(_data.rx,false,null,'KB')])
            // console.log(that.cont_chart_id.cpu.getOption());
            //实时更新图表数据
            that.cont_chart_id.cpu.setOption({
                series:[
                    {
                        name: 'CPU',
                        data: that.cont_chart.cpu_list
                    }
                ],
                xAxis:that.cont_chart.time_list
            })
            that.cont_chart_id.mem.setOption({
                series: [
                    {
                        name: lan.pythonmamager.mem,
                        data: that.cont_chart.mem_list['usage']
                    },
                    {
                        name: lan.site.cache,
                        data: that.cont_chart.mem_list['cache']
                    }
                ]
            })
            that.cont_chart_id.disk.setOption({
                series: [
                    {
                        name: lan.files.file_read,
                        data: that.cont_chart.disk_list['read']
                    },
                    {
                        name: lan.files.file_write,
                        data: that.cont_chart.disk_list['write']
                    }
                ]
            })
            that.cont_chart_id.network.setOption({
                series: [
                    {
                        name: lan.index.net_up,
                        data: that.cont_chart.network_list['tx']
                    },
                    {
                        name: lan.index.net_down,
                        data: that.cont_chart.network_list['rx']
                    }
                ]
            })
        })
    },
    /**
    * @description 容器监控【图表配置处理】
    * @param {String} type 图表类型【CPU/内存/磁盘/网络】
    * @return 返回处理好的图表配置
    */
    transform_cont_chart_option:function(type){
        var _unit = '/MB'
        var _option = this.get_default_option();
        switch(type){
            case 'cpu':
                _option.tooltip.formatter = function (config) {
                    var data = config[0];
                    return bt.format_data(data.data[0]) + '<br>' + data.seriesName + ': ' + data.data[1] + '%';
                };
                _option.yAxis.min = 0;
                _option.series = [
                    {
                        name: 'CPU',
                        type: 'line',
                        symbol: 'none',
                        smooth: true, 
                        itemStyle: {
                            normal: {
                                color: 'rgb(0, 153, 238)'
                            }
                        }
                    }
                ]
                break;
            case 'network':
                _unit = '/KB'
            case 'mem':
            case 'disk':
                var third = {
                    mem:[lan.pythonmamager.mem, lan.site.cache],
                    disk:[lan.files.file_read, lan.files.file_write],
                    network:[lan.index.net_up, lan.index.net_down],
                    color:[
                        {
                            mem:['rgb(185, 220, 253)','rgb(185, 220, 253,0.6)','rgb(185, 220, 253,0.3)','rgba(229,147,187)','rgba(229,147,187,0.6)','rgba(229,147,187,0.3)'],
                            disk:['rgb(255, 70, 131)','rgb(255, 70, 131,0.6)','rgb(255, 70, 131,0.3)','rgba(46, 165, 186)','rgba(46, 165, 186,0.6)','rgba(46, 165, 186,0.3)'],
                            network:['rgb(255, 140, 0)','rgb(255, 140, 0,0.6)','rgb(255, 140, 0,0.3)','rgb(30, 144, 255)','rgb(30, 144, 255,0.6)','rgb(30, 144, 255,0.3)']
                        }
                    ]
                }
                _option.tooltip.formatter = function (config) {
                    var data = config[0];
                    var time = data.data[0];
                    var date = bt.format_data(time / 1000);
                    var _tips = '';
                    var _style = '<span style="display: inline-block; width: 10px; height: 10px; margin-rigth:10px; border-radius: 50%; background: ';
                    for (var i = 0; i < config.length; i++) {
                        _tips +=  _style + config[i].color + ';"></span>  ' + config[i].seriesName + '：'
                        _tips += config[i].data[1] + _unit + (config.length - 1 !== i ? '<br />' : '');
                    }
                    return "时间：" + date + "<br />" + _tips;
                };
                _option.legend = {
                    top: '18px',
                    data: third[type]
                };
                _option.series = [
                    {
                        name: third[type][0],
                        type: 'line',
                        symbol: 'none',
                        itemStyle: {
                            normal: {
                                color: third['color'][0][type][0],
                                areaStyle: { 
                                    color: new echarts.graphic.LinearGradient(0, 1, 0, 0, [{
                                        offset: 0,
                                        color: third['color'][0][type][1]
                                    }, {
                                        offset: 1,
                                        color: third['color'][0][type][2]
                                    }])
                                }
                            }
                        }
                    },
                    {
                        name: third[type][1],
                        type: 'line',
                        symbol: 'none',
                        itemStyle: {
                            normal: {
                                color: third['color'][0][type][4],
                                areaStyle: { 
                                    color: new echarts.graphic.LinearGradient(0, 1, 0, 0, [{
                                        offset: 0,
                                        color: third['color'][0][type][4]
                                    }, {
                                        offset: 1,
                                        color: third['color'][0][type][5]
                                    }])
                                }
                            }
                        }
                    }
                  ];
                break;
        }
        return _option
    },
    /**
    * @description 渲染容器监控图表
    * @param {Object} row 容器信息
    */
    render_cont_chart:function(row){
        var that = this;
        this.cont_chart_id.cpu = echarts.init(document.getElementById('cont_cpu'))
        this.cont_chart_id.mem = echarts.init(document.getElementById('cont_mem'))
        this.cont_chart_id.disk = echarts.init(document.getElementById('cont_disk'))
        this.cont_chart_id.network = echarts.init(document.getElementById('cont_network'))
        
        $.each(['cpu','mem','disk','network'],function(index,item){
            that.cont_chart_id[item].setOption(that.transform_cont_chart_option(item))
        })
        this.transform_cont_chart_data(row) //默认加载数据
    },
    /**
    * @description 获取默认图表配置
    * @return 返回默认图表配置
    */
    get_default_option:function(){
        return {
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'cross'
                }
            },
            grid: {
                x: 50, //左
                y: 50, //上
                x2: 30,//右
                y2: 30 //下
            },
            xAxis: {
                type: 'time',
                scale:true,
                splitNumber:4,
                boundaryGap: true,
                axisLine: {
                    lineStyle: {
                        color: "#666"
                    }
                },
                axisLabel: {
                    // interval:0,
                    formatter: function (value) {
                        return bt.format_data(value / 1000, 'hh:mm:ss');
                    }
                },
            },
            yAxis: {
                type: 'value',
                boundaryGap: [0, '100%'],
                splitLine: {
                    lineStyle: {
                        color: "#ddd"
                    }
                },
                axisLine: {
                    lineStyle: {
                        color: "#666"
                    }
                }
            }
          }
    },
    /**
    * @description 容器详情配置
    * @param {Object} row 容器信息
    */
    open_container_config:function(obj){
        var that = this;
        layer.open({
            type:1,
            title:'Container ['+obj.name+']',
            area:['780px','720px'],
            shadeClose: false,
            closeBtn: 2,
            btn:false,
            content:'<div class="bt-tabs" style="height:100%">\
                <div class="bt-w-menu cn_menu pull-left" style="height:100%">\
                    <p class="bgw" data-type="config">Container configuration</p>\
                    <p data-type="create_image">Generate mirror image</p>\
                </div>\
                <div id="container_box" class="bt-w-con pd15"></div>\
            </div>',
            success:function(){
                that.set_cont_config(obj);
                // 菜单事件
                $('.cn_menu p').click(function () {
                    $('#container_box').html('').removeAttr('style');
                    $(this).addClass('bgw').siblings().removeClass('bgw');
                    that['set_cont_'+$(this).data('type')](obj);
                })
            }
        })
    },
    /**
    * @description 容器终端
    * @param {Object} row 容器信息
    */
    open_container_shell_view:function(row){
			var that = this;
					web_shell();
			var shell = setInterval(function(){
				if($('.term-box').length == 0){
					pdata_socket['data'] = 'exit\n'
					socket.emit('webssh',pdata_socket);
					setTimeout(function(){socket.emit('webssh',pdata_socket['data']);},1000);
					clearInterval(shell);
				}
			},500);
			setTimeout(function(){
				that.ajax_task_method('docker_shell', {
					data: { container_id: row.id }, 
					tips: lan.docker.container.execute_container_command,
					model_name: { dk_model_name: 'container' }
				}, function (res) {
					if (res.status) {
						pdata_socket['data'] = 'clear && ' + res.msg +'\n'
						socket.emit('webssh',pdata_socket);
						setTimeout(function(){
							socket.emit('webssh',pdata_socket['data']);
						}, 1000);
					}else{
						bt_tools.msg(res)
					}
				})
			});
    },
    /**
    * @description 容器配置
    * @param {Object} row 容器信息
    */
    set_cont_config:function(row){
        $('#container_box').css({'padding-right':'25px','overflow':'overlay'});
        var wrapper = document.getElementById("container_box")
        jsonTree.create(row.detail,wrapper)
    },
    /**
    * @description 容器生成镜像 【可导出文件】
    * @param {Object} row 容器信息
    */
    set_cont_create_image:function(row){
        var that = this;
        bt_tools.form({
            el:'#container_box',
            form:[{
                label:'Mirror name',
                group:{
                    name:'repository',
                    type: 'text',
                    placeholder: 'Please enter the mirror name',
                    width:'350px'
                }
            },{
                label:'Tag',
                group:{
                    name:'tag',
                    type: 'text',
                    placeholder: 'Please enter the tag',
                    width:'350px'
                }
            },{
                label:'Submit description',
                group:{
                    name:'message',
                    type: 'text',
                    placeholder: 'Description before submission',
                    width:'350px'
                }
            },{
                label:'Author',
                group:{
                    name:'author',
                    type: 'text',
                    placeholder: 'Please enter the author',
                    width:'350px'
                }
            },{
                label: '',
                group: [{
                    type: 'button',
                    size: '',
                    name: 'cont_caimage_btn',
                    title: 'Generate mirror image',
                    event: function (formData) {
                        if(
                            formData.repository == '' || 
                            formData.tag == ''        ||
                            formData.message == ''    ||
                            formData.author == ''     
                        ){
                            return layer.msg('Please fill in the generated mirror information first',{icon:2})
                        }
                        formData['id'] = row.id
                        submitImage(formData)
                    }
                },{
                    type: 'button',
                    size: '',
                    name: 'cont_caimage_export_btn',
                    style: { 'display': 'block', 'margin-top': '15px' },
                    title: 'Export the compressed package after the image is generated',
                    event: function (formData) {
                        if(
                            formData.repository == '' || 
                            formData.tag == ''        ||
                            formData.message == ''    ||
                            formData.author == ''     
                        ){
                            return layer.msg('Please fill in the generated mirror information first',{icon:2})
                        }
                        bt_tools.open({
                            type: 1,
                            title: 'Export ['+row.name+'] mirror image',
                            area: '430px',
                            btn: ['Export', lan.site.no],
                            content: {
                                'class': "pd20",
                                form: [{
                                    label: "Path",
                                    group: {
                                        name: "path",
                                        type: "text",
                                        value: '',
                                        width: "240px",
                                        placeholder:'Please enter the mirror path',
                                        icon: {
                                            type: 'glyphicon-folder-open',
                                            event:function(){}
                                        }
                                    }
                                },{
                                    label: "File name",
                                    group: {
                                        name: "name",
                                        type: "text",
                                        value: formData.repository,
                                        width: "240px",
                                        disabled:true,
                                        placeholder:'Please enter the exposed file name',
                                        unit:'.tar'
                                    }
                                }]
                            },
                            yes: function (formD,indexs) {
                                if (formD.path === '') return bt_tools.msg('The path cannot be empty!', 2)
                                if (formD.name === '') return bt_tools.msg('Export file name cannot be empty!', 2)
                                
                                formData['id'] = row.id
                                formData['path'] = formD.path
                                formData['name'] = formD.name
                                submitImage(formData,indexs)
                            }
                        })
                    }
                }]
            }]
        })
        // 生成镜像   --导出文件
        function submitImage(form,closeView){
            that.ajax_task_method('commit',{data:form,tips:'Generate mirror image'},function(res){
                if(res.status){
                    if(closeView) layer.close(closeView)
                }
                bt_tools.msg(res)
            })
        }
    },
    /**
     * @description 容器状态设置
     * @param {String} type 设置状态
     * @param {String} id 容器id
     * @param {Object} table 需要重新渲染的表格
     */
    container_status_setting:function(type,id,table,is_compose){
        var config = {id:id},
            tips = {start:'Start up',stop:'Stop',pause:'Pause',unpause:'Unpause',restart:'Restart',reload:'Reload'},
            param = {tips:tips[type]+' container'}
        if(is_compose){
            param['model_name'] = {dk_model_name:'container'}
        } 
        param['data'] = config;

        this.ajax_task_method(type,param,function(res){
            if(res.status){
                table.$refresh_table_list(true)  //刷新列表
            } 
            layer.msg(res.msg,{icon:res.status?1:2})
        })
    },
    /**
    * @description 获取日志窗口状态
    */
    get_log_situation:function(){
        var that = this;
        that.log_layer_open = layer.open({
            title: lan.docker.public.execution,
            type: 1,
            closeBtn: false,
            maxmin: true,
            skin: 'dockertmp',
            area: ["730px", '450px'],
            content:"<pre style='width:100%;margin-bottom: 0px;height:100%;border-radius:0px; text-align: left;background-color: #000;color: #fff;white-space: pre-wrap;' id='dockertmp_pre'></pre>",
            success:function(){
                that.log_file_setInterval = setInterval(function(){that.get_log_speed()},1500)
            }
        })
    },
    /**
    * @description 获取日志进度
    */
    get_log_speed:function(){
        this.ajax_task_method('get_logs',{data:{logs_file:'/tmp/dockertmp.log'},tips:false,model_name:{dk_model_name:"image"}},function(ires){
            $("#dockertmp_pre").text(ires.msg);
            $('#dockertmp_pre').animate({
                scrollTop: $('#dockertmp_pre').prop("scrollHeight")
            }, 400);
        })
    },
    /**
    * @description 删除容器监控数据和图表dom
    */
    remove_cont_chart_data:function(){
        clearInterval(this.cont_setInterval)
        this.cont_chart = {    
            cpu_list:[],
            mem_list:{
                usage:[],
                cache:[]
            },
            disk_list:{
                read:[],
                write:[]
            },
            network_list:{
                tx:[],
                rx:[]
            },
            time_list:[]
        }
        this.cont_chart_id = {
            cpu:null,
            mem:null,
            disk:null,
            network:null
        }
    },
    //删除日志定时器
    remove_log_clearinterval:function(){
        layer.close(layer.index)   //最新的弹层
        clearInterval(this.log_file_setInterval)
    },
    /**
    * @description 停止用户操作
    * @param {Boolean} is_install 是否docker安装
    * @param {Boolean} is_service 是否启动docker
    */
    stop_user_operation:function(is_install,is_service){
        var that = this;
        var tips = 'Docker service is not currently started. Please enable it in <a class="btlink setting_docker">Docker Settings</a>';
        if(!is_install) tips = 'Currently not installed docker or docker-compose, <a class="btlink install_docker">click install</a>'
        $('.mask_layer').removeAttr('style');
        $('.prompt_description').html(tips)
        //安装docker
        $('.install_docker').click(function(){
            that.ajax_task_method('install_docker_program',{model_name:{dk_model_name:'setup'}},function(res){
                bt_tools.msg(res)
                messagebox()
            })
        });
				$('.setting_docker').click(function () {
					$('.tab-list .tabs-item[data-type="setup"]').click()
				})
    },
    /**
     * @description docker请求方式转换
     * @param {String} action 请求方法
     * @param {Object} param data填写请求所需参数，tips填写请求时展示文字
     * @param {any} callback 数据回调
     */
    ajax_task_method:function(action,param,callback){
        var _config = $.extend({},param['data'] || {},this.global,{dk_def_name:action},param['model_name'] || {})
        bt_tools.send({
            url:this.global_api+'?action='+_config.dk_model_name+'-'+_config.dk_def_name+'',
            data:{data:JSON.stringify(_config)}
        },function(res){
            if(callback)callback(res)
        },{load:param['tips'],verify: false})
    },
    /**
     * @description docker批量操作参数处理
     * @param {String} action 请求方法
     * @param {Object} param 请求所需参数
     * @return 返回JSON格式参数
     */
    batch_param_convert:function(action,param){
        return JSON.stringify($.extend({},this.global,{dk_def_name:action},param || {}))
    },
    /**
     * @description UTC时间转换
     * @param {Object} utc_datetime utc时间
     * @return 返回处理后的时间
     */
    utc2beijing:function(utc_datetime) {
        // 转为正常的时间格式 年-月-日 时:分:秒
        var T_pos = utc_datetime.indexOf('T');
        var Z_pos = utc_datetime.indexOf('Z');
        var year_month_day = utc_datetime.substr(0,T_pos);
        var hour_minute_second = utc_datetime.substr(T_pos+1,Z_pos-T_pos-1);
        var new_datetime = year_month_day+" "+hour_minute_second; 
    
        // 处理成为时间戳
        timestamp = new Date(Date.parse(new_datetime));
        timestamp = timestamp.getTime();
        timestamp = timestamp/1000;
    
        // 增加8个小时，北京时间比utc时间多八个时区
        var timestamp = timestamp+8*60*60;
        return bt.format_data(timestamp)
    },
    initTabConfig:function(type){
        this.tabName = type;
        this.global.dk_model_name = type
        if(type == 'model') this.global.dk_model_name = 'compose'
        $('.mask_layer').hide();          //隐藏未安装或未启动提醒
        $('#dk_'+type+'_table').empty();  //清除Table
        this['get_'+type]();
    }
}
//默认触发
$('#cutMode .tabs-item[data-type="' + (bt.get_cookie('docker_model') || 'container') + '"]').trigger('click');