bt.pub.check_install(function (rdata) {
    if (rdata === false) bt.index.rec_install();
})
var interval_stop = false;
var index = {
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
                if (!interval_stop) index.get_data_info();
            }, 3000)
        },
        reload: function () {
            var _this = this;
            if (_this) clearInterval(_this.task_id);
            _this.start();
        }
    },
    net: {
        table: null,
        data: {
            uData: [],
            dData: [],
            aData: []
        },
        init: function () {
            //流量图表
            index.net.table = echarts.init(document.getElementById('NetImg'));
            var obj = {};
            obj.dataZoom = [];
            obj.unit = lan.index.unit + ':KB/s';
            obj.tData = index.net.data.aData;

            obj.list = [];
            obj.list.push({ name: lan.index.net_up, data: index.net.data.uData, circle: 'circle', itemStyle: { normal: { color: '#f7b851' } }, areaStyle: { normal: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(255, 140, 0,0.5)' }, { offset: 1, color: 'rgba(255, 140, 0,0.8)' }], false) } }, lineStyle: { normal: { width: 1, color: '#aaa' } } });
            obj.list.push({ name: lan.index.net_down, data: index.net.data.dData, circle: 'circle', itemStyle: { normal: { color: '#52a9ff' } }, areaStyle: { normal: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(30, 144, 255,0.5)' }, { offset: 1, color: 'rgba(30, 144, 255,0.8)' }], false) } }, lineStyle: { normal: { width: 1, color: '#aaa' } } });
            option = bt.control.format_option(obj)

            index.net.table.setOption(option);
            window.addEventListener("resize", function () {
                index.net.table.resize();
            });
        },
        add: function (up, down) {
            var _net = this;
            var limit = 8;
            var d = new Date()

            if (_net.data.uData.length >= limit) _net.data.uData.splice(0, 1);
            if (_net.data.dData.length >= limit) _net.data.dData.splice(0, 1);
            if (_net.data.aData.length >= limit) _net.data.aData.splice(0, 1);

            _net.data.uData.push(up);
            _net.data.dData.push(down);
            _net.data.aData.push(d.getHours() + ':' + d.getMinutes() + ':' + d.getSeconds());
        }
    },
    mem: {
        status: 1,
        set_status: function (obj, status, val) {
            var _this = this;
            _this.status = status;
            var _div = $('<div><span style="display:none">1</span></div>')
            if (status == 2) {
                obj.find(".mem-re-con").animate({ "top": "-400px", opacity: 0 }); //动画
                var btlen = parseInt(obj.find('.occupy span').html());
                for (var i = 0; i < btlen; i++) {
                    setTimeout(index.set_val(obj.parents('li'), { usage: btlen - i }), i * 30);
                };
                obj.addClass("mem-action");
                obj.find('.occupy').html(_div.append(lan.index.memre_ok_0 + ' <img src="/static/img/ings.gif">').html());
            }
            else if (status == 1) { //完成
                obj.removeClass('mem-action');
                obj.find('.occupy').removeClass('line').html("<span>" + val + "</span>%");
            }
            else {
                obj.find('.occupy').html(_div.append(status).html());
                if (bt.contains(status, '<br>')) obj.find('.occupy').addClass('line')
            }
        }
    },
    get_init: function () {
        var _this = this;
        setTimeout(function () { _this.get_disk_list(); }, 500)
        setTimeout(function () { _this.get_server_info(); }, 1000)


        bt.pub.get_user_info(function (rdata) {
            if (rdata.status) {
                $(".bind-user").html(rdata.data.username);
                bt.send('check_user_auth', 'ajax/check_user_auth', {}, function (rd) {
                    if (!rd.status) bt.msg(rd);
                });
                bt.weixin.get_user_info(function (rdata) {
                    if (!rdata.status) {
                        bt.msg(rdata);
                        return;
                    }
                    if (JSON.stringify(rdata.msg) != '{}') {
                        var datas = rdata.msg;
                        for (var key in datas) {
                            var item = datas[key];
                            item.nickName
                            $(".bind-weixin a").text(item.nickName);
                            break;
                        }
                    }
                });

            }
            else {
                $(".bind-weixin a").attr("href", "javascript:;");
                $(".bind-weixin a").click(function () {
                    bt.msg({ msg: lan.index.bind_bt_account_first, icon: 2 });
                })
            }
        })

        _this.get_data_info(function (loadbox, rdata) {
            loadbox.find('.cicle').hover(function () {
                var _this = $(this);
                var d = _this.parents('ul').data('data').load;
                layer.tips(lan.index.avg_load_atlast_onemin + d.one + '</br>'+ lan.index.avg_load_atlast_fivemin + d.five + '</br>'+ lan.index.avg_load_atlast_fifteenmin + d.fifteen + '', _this, { time: 0, tips: [1, '#999'] });
            }, function () {
                layer.closeAll('tips');
            })

            $('.cpubox').find('.cicle').hover(function () {
                var _this = $(this);
                var d = _this.parents('ul').data('data').cpu;
                var crs = '';
                var n1 = 0;
                for (var i = 0; i < d[2].length; i++) {
                    n1++;
                    crs += 'CPU-' + i + ": " + d[2][i] + '%' + (n1 % 2 == 0?'</br>':' | ');

                }
                layer.tips(d[3] + "</br>" + d[5] + " CPU, " + d[4] + " Core, " + d[4]+" Thread</br>"+ crs, _this, { time: 0, tips: [1, '#999'] });
            }, function () {
                layer.closeAll('tips');
            });

            $(".mem-release").hover(function () {
                $(this).addClass("shine_green");
                if (!($(this).hasClass("mem-action"))) {
                    $(this).find(".mem-re-min").hide();
                    $(this).find(".occupy").css({ "color": "#d2edd8" });
                    $(this).find(".mem-re-con").css({ "display": "block" });
                    $(this).find(".mem-re-con").animate({ "top": "0", opacity: 1 });
                }
				$(this).next().hide();
            }, function () {
                if (!($(this).hasClass("mem-action"))) {
                    $(this).find(".mem-re-min").show();
                }
                else {
                    return false;
                    //$(this).find(".mem-re-min").hide();
                }
                $(this).removeClass("shine_green");
                $(this).find(".occupy").css({ "color": "#20a53a" });
                $(this).find(".mem-re-con").css({ "top": "15px", opacity: 1, "display": "none" });
				$(this).next().show();
                //$(this).next().html(bt.get_cookie("mem-before"));
            }).click(function () {
                if (($(this).hasClass("mem-action"))) return false;
                var _this = $(this);
                bt.show_confirm(lan.index.mem_release_sure, '<font style="color:red;">'+lan.index.mem_release_warn+'</font>', function () {
                    if (!(_this.hasClass("mem-action"))) {
						_this.next().hide();
						_this.find('.mem-re-min').hide();
                        var data = _this.parents('ul').data('data').mem;
                        index.mem.set_status(_this, 2); //释放中
                        bt.system.re_memory(function (nData) {
                            index.mem.set_status(_this, lan.index.memre_ok);
							
							_this.next().show();
                            setTimeout(function () {
                                var t = nData.memFree - data.memFree;
                                var m = lan.index.memre_ok_2;
                                if (t > 0) m = lan.index.memre_ok_1 + "<br>" + t + "MB";
                                index.mem.set_status(_this, m);
                            }, 200);
                            setTimeout(function () { 
								index.mem.set_status(_this, 1, (nData.memRealUsed * 100 / nData.memTotal).toFixed(1)); 
								_this.find('.mem-re-min').show();
							}, 1200);
                        })
                    }
                })
            })
        });
        setTimeout(function () { _this.interval.start(); }, 1600)
        setTimeout(function () { index.get_index_list(); }, 1200)


        setTimeout(function () {
            _this.net.init();
        }, 200);

        setTimeout(function () {
            bt.system.check_update(function (rdata) {
                //console.log(rdata);
                if (rdata.status !== false) {
                    $('#toUpdate a').html(lan.index.update+'<i style="display: inline-block; color: red; font-size: 40px;position: absolute;top: -35px; font-style: normal; right: -8px;">.</i>');
                    $('#toUpdate a').css("position", "relative");

                }
                // if (rdata.msg.is_beta === 1) {
                //     $('#btversion').prepend('<span style="margin-right:5px;">Beta</span>');
                //     $('#btversion').append('<a class="btlink" href="https://www.bt.cn/bbs/forum-39-1.html" target="_blank">  ['+lan.index.find_bug_reward+']</a>');
                // }

            }, false)
        }, 1500)
    },
    get_data_info: function (callback) {
        var _this = $(this);
        bt.system.get_net(function (net) {

            var pub_arr = [{ val: 100, color: '#dd2f00' }, { val: 90, color: '#ff9900' }, { val: 70, color: '#20a53a' }, { val: 30, color: '#20a53a' }];
            var load_arr = [{ title: lan.index.run_block, val: 100, color: '#dd2f00' }, { title: lan.index.run_slow, val: 90, color: '#ff9900' }, { title: lan.index.run_normal, val: 70, color: '#20a53a' }, { title: lan.index.run_fluent, val: 30, color: '#20a53a' }];
            var _cpubox = $('.cpubox'), _membox = $('.membox'), _loadbox = $('.loadbox'), _diskbox = $('.diskbox')

            index.set_val(_cpubox, { usage: net.cpu[0], title: net.cpu[1]+' '+lan.index.cpu_core, items: pub_arr })
            index.set_val(_membox, { usage: (net.mem.memRealUsed * 100 / net.mem.memTotal).toFixed(1), items: pub_arr, title: net.mem.memRealUsed + '/' + net.mem.memTotal + '(MB)' })
            bt.set_cookie('memSize', net.mem.memTotal)
            for (var i = 0; i < _diskbox.length; i++) {
                index.set_val(_diskbox.eq(i), { usage: net.disk[i].size[3].split('%')[0], title: net.disk[i].size[1]+'/'+net.disk[0].size[0], items: pub_arr })
            }
            
            var _lval = Math.round((net.load.one / net.load.max) * 100);
            if (_lval > 100) _lval = 100;
            index.set_val(_loadbox, { usage: _lval, items: load_arr })
            _loadbox.parents('ul').data('data', net);

            //刷新流量
            $("#upSpeed").html(net.up + ' KB');
            $("#downSpeed").html(net.down + ' KB');
            $("#downAll").html(bt.format_size(net.downTotal));
            $("#upAll").html(bt.format_size(net.upTotal));
            index.net.add(net.up, net.down);
            if (index.net.table) index.net.table.setOption({ xAxis: { data: index.net.data.aData }, series: [{ name: lan.index.net_up, data: index.net.data.uData }, { name: lan.index.net_down, data: index.net.data.dData }] });

            if (callback) callback(_loadbox, net);
        })
    },
    get_server_info: function () {
        bt.system.get_total(function (info) {
            var memFree = info.memTotal - info.memRealUsed;
            if (memFree < 64) {
                $("#messageError").show();
                $("#messageError").append('<p><span class="glyphicon glyphicon-alert" style="color: #ff4040; margin-right: 10px;">' + lan.index.mem_warning + '</span> </p>')
            }

            if (info.isuser > 0) {
                $("#messageError").show();
                $("#messageError").append('<p><span class="glyphicon glyphicon-alert" style="color: #ff4040; margin-right: 10px;"></span>' + lan.index.user_warning + '<span class="c7 mr5" title="'+lan.index.safe_problem_cant_ignore+'" style="cursor:no-drop"> ['+lan.index.cant_ignore+']</span><a class="btlink" href="javascript:setUserName();"> ['+lan.index.edit_now+']</a></p>')
            }

            if (info.isport === true) {
                $("#messageError").show();
                $("#messageError").append('<p><span class="glyphicon glyphicon-alert" style="color: #ff4040; margin-right: 10px;"></span>'+lan.index.panel_port_tips+'<span class="c7 mr5" title="'+lan.index.panel_port_tip1+'" style="cursor:no-drop"> ['+lan.index.panel_port_tip2+']</span><a class="btlink" href="/config"> ['+lan.index.panel_port_tip3+']</a></p>')
            }
            var _system = info.system;
            $("#info").html(_system);
            $("#running").html(info.time);
            if (_system.indexOf("Windows") != -1) {
                $(".ico-system").addClass("ico-windows");
            }
            else if (_system.indexOf("CentOS") != -1) {
                $(".ico-system").addClass("ico-centos");
            }
            else if (_system.indexOf("Ubuntu") != -1) {
                $(".ico-system").addClass("ico-ubuntu");
            }
            else if (_system.indexOf("Debian") != -1) {
                $(".ico-system").addClass("ico-debian");
            }
            else if (_system.indexOf("Fedora") != -1) {
                $(".ico-system").addClass("ico-fedora");
            }
            else {
                $(".ico-system").addClass("ico-linux");
            }
        })
    },
    get_disk_list: function () {
        bt.system.get_disk_list(function (rdata) {
            if (rdata) {
                var data = { table: '#systemInfoList', items: [] };
                for (var i = 0; i < rdata.length; i++) {
                    var item = rdata[i];
                    var obj = {};
                    obj.name = item.path;
                    obj.title = item.size[1] + '/' + item.size[0];
                    obj.rate = item.size[3].replace('%', '');
                    obj.free = item.size[2];
                    var arr = [];
                    arr.push({ title: lan.index.inode_info, value: '' })
                    arr.push({ title: lan.index.total, value: item.inodes[0] })
                    arr.push({ title: lan.index.already_use, value: item.inodes[1] })
                    arr.push({ title: lan.index.available, value: item.inodes[2] })
                    arr.push({ title: lan.index.inode_percent, value: item.inodes[3] })
                    arr.push({ title: '<b>Capacity information</b>', value: '' })
                    arr.push({ title: 'Capacity', value: item.size[0] })
                    arr.push({ title: 'Used', value: item.size[1] })
                    arr.push({ title: 'Available', value: item.size[2] })
                    arr.push({ title: 'Usage rate', value: item.size[3] })
                    obj.masks = arr;
                    data.items.push(obj)
                }
                index.render_disk(data);
            }
        })
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
                    for (var j = 0; j < item.masks.length; j++) mask += item.masks[j].title + ': ' + item.masks[j].value + "<br>";
                    _li.data('mask', mask);
                    _li.find('.cicle').hover(function () {
                        var _this = $(this);
                        layer.tips(_this.parent().data('mask'), _this, { time: 0, tips: [1, '#999'] });
                    }, function () {
                        layer.closeAll('tips');
                    })
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
                        color = '#dd2f00'
                        break;
                }
                index.set_val(_li, { usage: item.rate, color: color })
                _tab.append(_li);
            }
        }
    },
    set_val: function (_li, obj) {
        //obj.usage = parseInt(obj.usage)
        if (obj.usage > 50) {
            setTimeout(function () { _li.find('.bar-right-an').css({ "transform": "rotate(45deg)", "transition": "transform 750ms linear" }); }, 10)
            setTimeout(function () { _li.find('.bar-left-an').css({ "transform": "rotate(" + (((obj.usage - 50) / 100 * 360) - 135) + "deg)", "transition": "transform 750ms linear" }); }, 760);
        } else {
            if (parseInt(_li.find('.occupy span').html()) > 50) {
                setTimeout(function () { _li.find('.bar-right-an').css({ "transform": "rotate(" + ((obj.usage / 100 * 360) - 135) + "deg)", "transition": "transform 750ms linear" }) }, 760);
                setTimeout(function () { _li.find('.bar-left-an').css({ "transform": "rotate(-135deg)", "transition": "transform 750ms linear" }) }, 10)
            } else {
                setTimeout(function () { _li.find('.bar-right-an').css({ "transform": "rotate(" + ((obj.usage / 100 * 360) - 135) + "deg)", "transition": "transform 750ms linear" }); }, 10)
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
    get_index_list: function () {
        bt.soft.get_index_list(function (rdata) {
            var con = '';
            var icon = '';
            var rlen = rdata.length;
            var clickName = '';
            var setup_length = 0;
            for (var i = 0; i < rlen; i++) {
                if (rdata[i].setup) {
                    setup_length++;
                    if (rdata[i].admin) {
                        clickName = ' onclick="bt.soft.set_lib_config(\'' + rdata[i].name + '\',\'' + rdata[i].title + '\')"';
                    }
                    else {
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
                        status = '<span style="color:red" class="glyphicon glyphicon-pause"></span>'
                    }
                    con += '<div class="col-sm-3 col-md-3 col-lg-3" data-id="' + rdata[i].name + '">\
							<span class="spanmove"></span>\
							<div '+ clickName + '>\
							<div class="image"><img width="48" src="/static/img/soft_ico/ico-'+ icon + '.png"></div>\
							<div class="sname">'+ rdata[i].title + ' ' + rdata[i].version + status + '</div>\
							</div>\
						</div>'
                }
            }
            $("#indexsoft").html(con);
            //软件位置移动
            var softboxsum = 12;
            var softboxcon = '';
            if (setup_length <= softboxsum) {
                for (var i = 0; i < softboxsum - setup_length; i++) {
                    softboxcon += '<div class="col-sm-3 col-md-3 col-lg-3 no-bg"></div>'
                }
                $("#indexsoft").append(softboxcon);
            }
            $("#indexsoft").dragsort({ dragSelector: ".spanmove", dragBetween: true, dragEnd: saveOrder, placeHolderTemplate: "<div class='col-sm-3 col-md-3 col-lg-3 dashed-border'></div>" });

            function saveOrder() {
                var data = $("#indexsoft > div").map(function () { return $(this).attr("data-id"); }).get();
                data = data.join('|');
                bt.soft.set_sort_index(data)
            };
        })
    },
    check_update: function () {
    	var _load = bt.load('Getting updates, please wait...');
        bt.system.check_update(function (rdata) {
        	_load.close();
            if (rdata.status === false) {
                if (!rdata.msg.beta) {
                    bt.msg(rdata);
                    return;
                }
                var loading = bt.open({
                    type: 1,
                    title: '[Linux' + (rdata.msg.is_beta == 1 ? lan.index.test_version : lan.index.final_version) + ']-'+lan.index.update_log,
                    area: '520px',
                    shadeClose: false,
                    skin: 'layui-layer-dialog',
                    closeBtn: 2,
                    content: '<div class="setchmod bt-form">\
                                <div class="update_title"><i class="layui-layer-ico layui-layer-ico1"></i><span>'+lan.index.last_version_now+'</span></div>\
                                <div class="update_version">'+lan.index.this_version+'<a href="https://forum.aapanel.com/d/9-aapanel-linux-panel-6-1-5-installation-tutorial/36" target="_blank" class="btlink" title="'+lan.index.check_this_version_log+'">'+lan.index.bt_linux+ (rdata.msg.is_beta == 1 ? lan.index.test_version+' ' + rdata.msg.beta.version : lan.index.final_version+' ' + rdata.msg.version) + '</a>&nbsp;&n'+ lan.index.release_time + (rdata.msg.is_beta == 1 ? rdata.msg.beta.uptime : rdata.msg.uptime) + '</div>\
                                <div class="bt-form-submit-btn">\
                                    <button type="button" class="btn btn-danger btn-sm btn-title" onclick="layer.closeAll()">'+ lan.public.cancel + '</button>\
                                    <button type="button" class="btn btn-success btn-sm btn-title btn_update_panel" onclick="layer.closeAll()">'+ lan.public.know + '</button>\
                                </div>\
                            </div>\
                            <style>\
                                .setchmod{padding-bottom:50px;}\
                                .update_title{overflow: hidden;position: relative;vertical-align: middle;margin-top: 10px;}\
                                .update_title .layui-layer-ico{display: block;left: 60px !important;top: 1px !important;}\
                                .update_title span{display: inline-block;color: #333;height: 30px;margin-left: 105px;margin-top: 3px;font-size: 20px;}\
                                .update_conter{background: #f9f9f9;border-radius: 4px;padding: 20px;margin: 15px 37px;margin-top: 15px;}\
                                .update_version{font-size: 12px;margin:15px 0 10px 85px}\
                                .update_logs{margin-bottom:10px;border-bottom:1px solid #ececec;padding-bottom:10px;}\
                                .update_tips{font-size: 13px;color: #666;font-weight: 600;}\
                                .update_tips span{padding-top: 5px;display: block;font-weight: 500;}\
                            </style>'
                });
                return;
            }
            if (rdata.status === true) {
                var result = rdata
                var is_beta = rdata.msg.is_beta
                if (is_beta) {
                    rdata = result.msg.beta
                } else {
                    rdata = result.msg
                }
                var loading = bt.open({
                    type: 1,
                    title: '[Linux' + (is_beta === 1 ? lan.index.test_version : lan.index.final_version) + ']-'+ lan.index.update_log,
                    area: '520px',
                    shadeClose: false,
                    skin: 'layui-layer-dialog',
                    closeBtn: 2,
                    content: '<div class="setchmod bt-form" style="padding-bottom:50px;">\
                                    <div class="update_title"><i class="layui-layer-ico layui-layer-ico0"></i><span>'+lan.index.have_new_version+'</span></div>\
                                    <div class="update_conter">\
                                        <div class="update_version">'+lan.index.last_version+'<a href="https://forum.aapanel.com/d/9-aapanel-linux-panel-6-1-5-installation-tutorial/36" target="_blank" class="btlink" title="'+lan.index.check_version_log+'">'+lan.index.bt_linux+ (is_beta === 1 ? lan.index.test_version : lan.index.final_version) + rdata.version + '</a></br>'+lan.index.update_date + (result.msg.is_beta == 1 ? result.msg.beta.uptime : result.msg.uptime) + '</div>\
                                        <div class="update_logs">'+ rdata.updateMsg + '</div>\
                                    </div>\
                                    <!--div class="update_conter">\
                                        <div class="update_tips">'+ (is_beta !== 1 ? lan.index.test_version : lan.index.final_version) + lan.index.last_version_is + (result.msg.is_beta != 1 ? result.msg.beta.version : result.msg.version) + '&nbsp;&nbsp;&nbsp;'+lan.index.update_time+'&nbsp;&nbsp;' + (is_beta != 1 ? result.msg.beta.uptime : result.msg.uptime) + '</div>\
                                        '+ (is_beta !== 1 ? '<span>'+lan.index.update_verison_click+'<a href="javascript:;" onclick="index.beta_msg()" class="btlink btn_update_testPanel">'+lan.index.check_detail+'</a></span>' : '<span>'+lan.index.change_final_click+'<a href="javascript:;" onclick="index.to_not_beta()" class="btlink btn_update_testPanel">'+lan.index.change_final+'</a></span>') + '\
                                    </div-->\
                                    <div class="bt-form-submit-btn">\
                                        <button type="button" class="btn btn-danger btn-sm btn-title" onclick="layer.closeAll()">'+ lan.public.cancel + '</button>\
                                        <button type="button" class="btn btn-success btn-sm btn-title btn_update_panel" onclick="index.to_update()" >'+ lan.index.update_go + '</button>\
                                    </div>\
                                </div>\
                                <style>\
                                    .update_title{overflow: hidden;position: relative;vertical-align: middle;margin-top: 10px;}.update_title .layui-layer-ico{display: block;left: 71px !important;top: 1px !important;}.update_title span{display: inline-block;color: #333;height: 30px;margin-left: 117px;margin-top: 3px;font-size: 20px;}.update_conter{background: #f9f9f9;border-radius: 4px;padding: 20px;margin: 15px 37px;margin-top: 15px;}.update_version{font-size: 13.5px; margin-bottom: 10px;font-weight: 600;}.update_logs{margin-bottom:10px;}.update_tips{font-size: 13px;color:#666;}.update_conter span{display: block;font-size:13px;color:#666}\
                                </style>'
                });
            }
        })
    },
    to_update: function () {
        layer.closeAll();
        bt.system.to_update(function (rdata) {
            if (rdata.status) {
                bt.msg({ msg: rdata.msg, icon: 1 })
                $("#btversion").html(rdata.version);
                $("#toUpdate").html('');
                bt.system.reload_panel();
                setTimeout(function () { window.location.reload(); }, 3000);
            }
            else {
                bt.msg({ msg: rdata.msg, icon: 5, time: 5000 });
            }
        });
    },
    to_not_beta: function () {
        bt.show_confirm(lan.index.change_final,lan.index.change_test_to_final, function () {

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
        bt.send('get_beta_logs', 'ajax/get_beta_logs', {}, function (data) {
            var my_list = '';
            for (var i = 0; i < data.list.length; i++) {
                my_list += '<div class="item_list">\
                                            <span class="index_acive"></span>\
                                            <div class="index_date">'+ bt.format_data(data.list[i].uptime).split(' ')[0] + '</div>\
                                            <div class="index_title">'+ data.list[i].version + '</div>\
                                            <div class="index_conter">'+ data.list[i].upmsg + '</div>\
                                        </div>'
            }
            layer.open({
                type: 1,
                title: lan.index.apply_linux_test_version,
                area: '650px',
                shadeClose: false,
                skin: 'layui-layer-dialog',
                closeBtn: 2,
                content: '<div class="bt-form pd20" style="padding-bottom:50px;padding-top:0">\
                            <div class="bt-form-conter">\
                                <span style="font-weight: 600;">'+lan.index.apply_most_know+'</span>\
                                <div class="form-body">'+ data.beta_ps + '</div>\
                            </div>\
                            <div class="bt-form-conter">\
                                <span style="font-size:16px;">'+lan.index.linux_test_version_update_log+'</span>\
                                <div class="item_box"  style="height:180px;overflow: auto;">'+ my_list + '</div>\
                            </div>\
                            <div class="bt-form-line"> <label for="notice" style="cursor: pointer;"><input id="notice" disabled="disabled" type="checkbox" style="vertical-align: text-top;margin-right:5px"></input><span style="font-weight:500">'+lan.index.already_read+lan.index.apply_most_know1+'<i id="update_time"></i></span></label>\</div>\
                            <div class="bt-form-submit-btn">\
                                <button type="button" class="btn btn-danger btn-sm btn-title" onclick="layer.closeAll()">'+ lan.public.cancel + '</button>\
                                <button type="button" class="btn btn-success btn-sm btn-title btn_update_panel_beta" disabled>'+ lan.index.update_go + '</button>\
                            </div>\
                            <style>\
                                .bt-form-conter{padding: 20px 25px;line-height: 29px;background: #f7f7f7;border-radius: 5px;padding-bottom:30px;margin-bottom:20px;}\
                                .bt-form-conter span{margin-bottom: 10px;display: block;font-size: 19px;text-align: center;color: #333;}\
                                .form-body{color: #333;}\
                                #notice span{cursor: pointer;}\
                                #update_time{font-style:normal;color:red;}\
                                .item_list{margin-left:95px;border-left:5px solid #e1e1e1;position:relative;padding:5px 0 0 2px}.index_title{border-bottom:1px solid #ececec;margin-bottom:5px;font-size:15px;color:#20a53a;padding-left:15px;margin-top:7px;margin-left:5px}.index_conter{line-height:25px;font-size:12px;min-height:40px;padding-left:20px;color:#888}.index_date{position:absolute;left:-90px;top:13px;font-size:13px;color:#333}.index_acive{width:15px;height:15px;background-color:#20a53a;display:block;border-radius:50%;position:absolute;left:-10px;top:21px}.index_acive::after{position:relative;display:block;content:"";height:5px;width:5px;display:block;border-radius:50%;background-color:#fff;top:5px;left:5px}\
                            </style>\
                        </div>'
            });
            var countdown = 5;
            function settime(val) {
                if (countdown == 0) {
                    val.removeAttr("disabled");
                    $('#update_time').text('');
                    return false;
                } else {
                    $('#update_time').text(lan.index.second_left_of_click.replace('{1}',countdown));
                    countdown--;
                    setTimeout(function () {
                        settime(val)
                    }, 1000)
                }
            }
            settime($('#notice'));
            $('#notice').click(function () {
                console.log($(this).prop('checked'))
                if ($(this).prop('checked')) {
                    $('.btn_update_panel_beta').removeAttr('disabled');
                } else {
                    $('.btn_update_panel_beta').attr('disabled', 'disabled');
                }
            });
            $('.btn_update_panel_beta').click(function () {
                bt.show_confirm(lan.index.update_test_version, lan.index.check_test_version_detail, function () {

                    bt.send('apple_beta', 'ajax/apple_beta', {}, function (rdata) {
                        if (rdata.status === false) {
                            bt.msg(rdata);
                            return;
                        }
                        bt.system.check_update(function (rdata) {
                            index.to_update();
                        });
                    });
                });
            })
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
            })
        });
    },
    re_server: function () {
        bt.open({
            type: 1,
            title: lan.index.restart_serverorpanel,
            area: '330px',
            closeBtn: 2,
            shadeClose: false,
            content: '<div class="rebt-con"><div class="rebt-li"><a data-id="server" href="javascript:;">'+lan.index.restart_server+'</a></div><div class="rebt-li"><a data-id="panel" href="javascript:;">'+lan.index.restart_panel+'</a></div></div>'
        })
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
                            setTimeout(function () { window.location.reload(); }, 3000);
                        });
                        break;
                    case 'server':
                        var rebootbox = bt.open({
                            type: 1,
                            title: lan.index.reboot_title,
                            area: ['500px', '280px'],
                            closeBtn: 2,
                            shadeClose: false,
                            content: "<div class='bt-form bt-window-restart'>\
									<div class='pd15'>\
									<p style='color:red; margin-bottom:10px; font-size:15px;'>"+ lan.index.reboot_warning + "</p>\
									<div class='SafeRestart' style='line-height:26px'>\
										<p>"+ lan.index.reboot_ps + "</p>\
										<p>"+ lan.index.reboot_ps_1 + "</p>\
										<p>"+ lan.index.reboot_ps_2 + "</p>\
										<p>"+ lan.index.reboot_ps_3 + "</p>\
										<p>"+ lan.index.reboot_ps_4 + "</p>\
									</div>\
									</div>\
									<div class='bt-form-submit-btn'>\
										<button type='button' class='btn btn-danger btn-sm btn-reboot'>"+ lan.public.cancel + "</button>\
										<button type='button' class='btn btn-success btn-sm WSafeRestart' >"+ lan.public.ok + "</button>\
									</div>\
								</div>"
                        });
                        setTimeout(function () {
                            $(".btn-reboot").click(function () {
                                rebootbox.close();
                            })
                            $(".WSafeRestart").click(function () {
                                var body = '<div class="SafeRestartCode pd15" style="line-height:26px"></div>';
                                $(".bt-window-restart").html(body);
                                $(".SafeRestartCode").append("<p>" + lan.index.reboot_msg_1 + "</p>");
                                bt.pub.set_server_status_by("name={{session['webserver']}}&type=stop", function (r1) {
                                    $(".SafeRestartCode p").addClass('c9');
                                    $(".SafeRestartCode").append("<p>" + lan.index.reboot_msg_2 + "...</p>");
                                    bt.pub.set_server_status_by("name=mysqld&type=stop", function (r2) {
                                        $(".SafeRestartCode p").addClass('c9');
                                        $(".SafeRestartCode").append("<p>" + lan.index.reboot_msg_3 + "...</p>");
                                        bt.system.root_reload(function (rdata) {
                                            $(".SafeRestartCode p").addClass('c9');
                                            $(".SafeRestartCode").append("<p>" + lan.index.reboot_msg_4 + "...</p>");
                                            var sEver = setInterval(function () {
                                                bt.system.get_total(function () {
                                                    clearInterval(sEver);
                                                    $(".SafeRestartCode p").addClass('c9');
                                                    $(".SafeRestartCode").append("<p>" + lan.index.reboot_msg_5 + "...</p>");
                                                    setTimeout(function () {
                                                        layer.closeAll();
                                                    }, 3000);
                                                })
                                            }, 3000);
                                        })
                                    })
                                })
                            })
                        }, 100)
                        break;
                }
            })
        }, 100)
    },
    open_log: function () {
        bt.open({
            type: 1,
            area: '640px',
            title: lan.index.update_log,
            closeBtn: 2,
            shift: 5,
            shadeClose: false,
            content: '<div class="DrawRecordCon"></div>'
        });
        $.get('https://www.bt.cn/Api/getUpdateLogs?type=' + bt.os, function (rdata) {
            var body = '';
            for (var i = 0; i < rdata.length; i++) {
                body += '<div class="DrawRecord DrawRecordlist">\
							<div class="DrawRecordL">'+ rdata[i].addtime + '<i></i></div>\
							<div class="DrawRecordR">\
								<h3>'+ rdata[i].title + '</h3>\
								<p>'+ rdata[i].body + '</p>\
							</div>\
						</div>'
            }
            $(".DrawRecordCon").html(body);
        }, 'jsonp');
    },
    get_cloud_list: function () {
        $.post('/plugin?action=get_soft_list', { type: 8, p: 1, force: 1, cache: 1 }, function (rdata) {
            console.log(lan.index.get_soft_list_success);
        });
    }
}
index.get_init();
//setTimeout(function () { index.get_cloud_list() }, 800);