var bt = {
    os: 'Linux',
    check_ip: function(ip) //验证ip
        {
            var reg = /^(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])$/;
            return reg.test(ip);
        },
    check_ips: function(ips) //验证ip段
        {
            var reg = /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(\/\d{1,2})?$/;
            return reg.test(ip);
        },
    check_url: function(url) //验证url
        {
            var reg = /^((https|http|ftp|rtsp|mms)?:\/\/)[^\s]+/;
            return reg.test(url);
        },
    check_port: function(port) {
        var reg = /^([1-9]|[1-9]\d|[1-9]\d{2}|[1-9]\d{3}|[1-5]\d{4}|6[0-4]\d{3}|65[0-4]\d{2}|655[0-2]\d|6553[0-5])$/;
        return reg.test(port);
    },
    check_chinese: function(str) {
        var reg = /[\u4e00-\u9fa5]/;
        return reg.test(str);
    },
    check_domain: function(domain) //验证域名
        {
            var reg = /^([\w\u4e00-\u9fa5\-\*]{1,100}\.){1,4}([\w\u4e00-\u9fa5\-]{1,24}|[\w\u4e00-\u9fa5\-]{1,24}\.[\w\u4e00-\u9fa5\-]{1,24})$/;
            return reg.test(bt.strim(domain));
        },
    check_img: function(fileName) //验证是否图片
        {
            var exts = ['jpg', 'jpeg', 'png', 'bmp', 'gif', 'tiff', 'ico'];
            var check = bt.check_exts(fileName, exts);
            return check;
        },
check_email: function (email) {
					var reg = /\w[-\w.+]*@([A-Za-z0-9][-A-Za-z0-9]+\.)+[A-Za-z]{2,14}/;
					return reg.test(email);
				},
				check_phone: function (phone) {
					var reg = /^1(3|4|5|6|7|8|9)\d{9}$/;
					return reg.test(phone);
				},
    check_zip: function(fileName) {
        var ext = fileName.split('.');
        var extName = ext[ext.length - 1].toLowerCase();
        if (extName == 'zip') return 0;
        if (extName == 'rar') return 2;
        if (extName == 'gz' || extName == 'tgz') return 1;
        return -1;
    },
    clear_cookie:function(key){
	    this.set_cookie(key,'',new Date());
	},
    check_text: function(fileName) {
        var exts = ['rar', 'zip', 'tar.gz', 'gz', 'iso', 'xsl', 'doc', 'xdoc', 'jpeg', 'jpg', 'png', 'gif', 'bmp', 'tiff', 'exe', 'so', '7z', 'bz'];
        return bt.check_exts(fileName, exts) ? false : true;
    },
    check_exts: function(fileName, exts) {
        var ext = fileName.split('.');
        if (ext.length < 2) return false;
        var extName = ext[ext.length - 1].toLowerCase();
        for (var i = 0; i < exts.length; i++) {
            if (extName == exts[i]) return true;
        }
        return false;
    },
    check_version: function(version, cloud_version) {
        var arr1 = version.split('.'); //
        var arr2 = cloud_version.split('.');
        var leng = arr1.length > arr2.length ? arr1.length : arr2.length;
        while (leng - arr1.length > 0) {
            arr1.push(0);
        }
        while (leng - arr2.length > 0) {
            arr2.push(0);
        }
        for (var i = 0; i < leng; i++) {
            // if (i == leng - 1) {
            //     if (arr1[i] != arr2[i]) return 2; //子版本匹配不上
            // } else {
            //     if (arr1[i] != arr2[i]) return -1; //版本匹配不上
            // }

            if (parseInt(arr1[i]) < parseInt(arr2[i])) {
                return 2;
            }
        }
        return 1; //版本正常
    },
    replace_all: function(str, old_data, new_data) {
        var reg_str = "/(" + old_data + "+)/g"
        var reg = eval(reg_str);
        return str.replace(reg, new_data);
    },
    get_file_ext: function(fileName) {
        var text = fileName.split(".");
        var n = text.length - 1;
        text = text[n];
        return text;
    },
    get_file_path: function(filename) {
        var arr = filename.split('/');
        path = filename.replace('/' + arr[arr.length - 1], "");
        return path;
    },
    get_date: function(a) {
        var dd = new Date();
        dd.setTime(dd.getTime() + (a == undefined || isNaN(parseInt(a)) ? 0 : parseInt(a)) * 86400000);
        var y = dd.getFullYear();
        var m = dd.getMonth() + 1;
        var d = dd.getDate();
        return y + "-" + (m < 10 ? ('0' + m) : m) + "-" + (d < 10 ? ('0' + d) : d);
    },
    get_form: function(select) {
        var sarr = $(select).serializeArray();
        var iarr = {}
        for (var i = 0; i < sarr.length; i++) {
            iarr[sarr[i].name] = sarr[i].value;
        }
        return iarr;
    },
    ltrim: function(str, r) {
        var reg_str = "/(^\\" + r + "+)/g"
        var reg = eval(reg_str);
        str = str.replace(reg, "");
        return str;
    },
    rtrim: function(str, r) {
        var reg_str = "/(\\" + r + "+$)/g"
        var reg = eval(reg_str);
        str = str.replace(reg, "");
        return str;
    },
    strim: function(str) {
        var reg_str = "/ /g"
        var reg = eval(reg_str);
        str = str.replace(reg, "");
        return str;
    },
    contains: function(str, substr) {
        if (str) {
            return str.indexOf(substr) >= 0;
        }
        return false;
    },
    format_size: function(bytes, is_unit, fixed, end_unit) //字节转换，到指定单位结束 is_unit：是否显示单位  fixed：小数点位置 end_unit：结束单位
        {
            if (bytes == undefined) return 0;

            if (is_unit == undefined) is_unit = true;
            if (fixed == undefined) fixed = 2;
            if (end_unit == undefined) end_unit = '';

            if (typeof bytes == 'string') bytes = parseInt(bytes);
            var unit = [' B', ' KB', ' MB', ' GB', 'TB'];
            var c = 1024;
            for (var i = 0; i < unit.length; i++) {
                var cUnit = unit[i];
                if (end_unit) {
                    if (cUnit.trim() == end_unit.trim()) {
                        var val = i == 0 ? bytes : fixed == 0 ? bytes : bytes.toFixed(fixed)
                        if (is_unit) {
                            return val + cUnit;
                        } else {
                            val = parseFloat(val);
                            return val;
                        }
                    }
                } else {
                    if (bytes < c) {
                        var val = i == 0 ? bytes : fixed == 0 ? bytes : bytes.toFixed(fixed)
                        if (is_unit) {
                            return val + cUnit;
                        } else {
                            val = parseFloat(val);
                            return val;
                        }
                    }
                }

                bytes /= c;
            }
        },
    format_data: function(tm, format) {
        if (format == undefined) format = "yyyy/MM/dd hh:mm:ss";
        tm = tm.toString();
        if (tm.length > 10) {
            tm = tm.substring(0, 10);
        }
        var data = new Date(parseInt(tm) * 1000);
        var o = {
            "M+": data.getMonth() + 1, //month
            "d+": data.getDate(), //day
            "h+": data.getHours(), //hour
            "m+": data.getMinutes(), //minute
            "s+": data.getSeconds(), //second
            "q+": Math.floor((data.getMonth() + 3) / 3), //quarter
            "S": data.getMilliseconds() //millisecond
        }
        if (/(y+)/.test(format)) format = format.replace(RegExp.$1,
            (data.getFullYear() + "").substr(4 - RegExp.$1.length));
        for (var k in o)
            if (new RegExp("(" + k + ")").test(format))
                format = format.replace(RegExp.$1,
                    RegExp.$1.length == 1 ? o[k] : ("00" + o[k]).substr(("" + o[k]).length));

        return format;
    },
    format_path: function(path) {
        var reg = /(\\)/g;
        path = path.replace(reg, '/');
        return path;
    },
    get_random: function(len) {
        len = len || 32;
        var $chars = 'AaBbCcDdEeFfGHhiJjKkLMmNnPpRSrTsWtXwYxZyz2345678'; // 默认去掉了容易混淆的字符oOLl,9gq,Vv,Uu,I1  
        var maxPos = $chars.length;
        var pwd = '';
        for (i = 0; i < len; i++) {
            pwd += $chars.charAt(Math.floor(Math.random() * maxPos));
        }
        return pwd;
    },
    refresh_pwd: function(length, obj) {
        if (obj == undefined) obj = 'MyPassword';
        var _input = $("#" + obj);
        if (_input.length > 0) {
            _input.val(bt.get_random(length))
        } else {
            $("." + obj).val(bt.get_random(length))
        }
    },
    get_random_num: function(min, max) //生成随机数
        {
            var range = max - min;
            var rand = Math.random();
            var num = min + Math.round(rand * range); //四舍五入
            return num;
        },

  /**
   * 生成计算数字(加强计算，用于删除重要数据二次确认)
   * */
  get_random_code: function () {
    var flist = [20, 21, 22, 23]

    var num1 = bt.get_random_num(13, 19);
    var t1 = num1 % 10;

    var num2 = bt.get_random_num(13, 29);
    var t2 = num2 % 10;

    while ($.inArray(num2, flist) >= 0 || (t1 + t2) <= 10 || t1 == t2) {
      num2 = bt.get_random_num(13, 29);
      t2 = num2 % 10;
    }
    return { 'num1': num1, 'num2': num2 }
  },
    /**
     * @description 设置本地存储，local和session
     * @param {String} type 存储类型，可以为空，默认为session类型。
     * @param {String} key 存储键名
     * @param {String} val 存储键值
     * @return 无返回值
     */
    set_storage: function (type, key, val) {
        if (type != "local" && type != "session") val = key, key = type, type = 'local';
        window[type + 'Storage'].setItem(key, val);
    },


    /**
     * @description 获取本地存储，local和session
     * @param {String} type 存储类型，可以为空，默认为session类型。
     * @param {String} key 存储键名
     * @return {String} 返回存储键值
     */
    get_storage: function (type, key) {
        if (type != "local" && type != "session") key = type, type = 'local';
        return window[type + 'Storage'].getItem(key);
    },

    /**
     * @description 删除指定本地存储，local和session
     * @param {String} type 类型，可以为空，默认为session类型。
     * @param {String} key 键名
     * @return 无返回值
     */
    remove_storage: function (type, key) {
        if (type != "local" && type != "session") key = type, type = 'local';
        window[type + 'Storage'].removeItem(key);
    },

    /**
     * @description 删除指定类型的所有存储信息储，local和session
     * @param {String} type 类型，可以为空，默认为session类型。
     * @return 无返回值
     */
    clear_storage: function (type) {
        if (type != "local" && type != "session") key = type, type = 'local';
        window[type + 'Storage'].clear();
    },
	set_cookie : function(key,val,time)
	{
		if(time != undefined){
			var exp = new Date();
			exp.setTime(exp.getTime() + time);
			time = exp.toGMTString();
		}else{
			var Days = 30;
			var exp = new Date();
			exp.setTime(exp.getTime() + Days*24*60*60*1000);
			time = exp.toGMTString();
		}
		document.cookie = key + "="+ escape (val) + ";expires=" + time;
	},
    get_cookie: function(key) {
        var arr, reg = new RegExp("(^| )" + key + "=([^;]*)(;|$)");
        if (arr = document.cookie.match(reg)) {
            var val = unescape(arr[2]);
            return val == 'undefined' ? '' : val;
        } else {
            return null;
        }
    },
    /**
   * @description 选择文件目录或文件
   * @param id {string} 元素ID
   * @param type {string || function} 选择方式，文件或目录
   * @param success {function} 成功后的回调
   */
    select_path: function(id, type,success,default_path) {
        _this = this;
        _this.set_cookie("SetName", "");
        if (typeof type !== 'string') {
					success = type;
					type = 'dir';
				}
        var loadT = bt.open({
            type: 1,
            area: "680px",
            title: type === 'all' ? 'Select directories or files' : type === 'file' ? lan.bt.file : lan.bt.dir,
            closeBtn: 2,
            shift: 5,
            content: "<div class='changepath'><div class='path-top'><button type='button' id='btn_back' class='btn btn-default btn-sm'><span class='glyphicon glyphicon-share-alt'></span> " + lan.public.return + "</button><div class='place' id='PathPlace'>" + lan.bt.path + "：<span></span></div></div><div class='path-con'><div class='path-con-left'><dl><dt id='changecomlist' >" + lan.bt.comp + "</dt></dl></div><div class='path-con-right'><ul class='default' id='computerDefautl'></ul><div class='file-list divtable'><table id='file-list-table' class='table table-hover' style='border:0 none'><thead><tr class='file-list-head'><th width='5%'></th><th width='38%'>" + lan.bt.filename + "</th><th width='24%'>" + lan.bt.etime + "</th><th width='8%'>" + lan.bt.access + "</th><th width='15%'>" + lan.bt.own + "</th></tr></thead><tbody id='tbody' class='list-list'></tbody></table></div></div></div></div><div class='getfile-btn' style='margin-top:0'><button type='button' class='btn btn-default btn-sm pull-left' onclick='CreateFolder()'>" + lan.bt.adddir + "</button><button type='button' class='btn btn-danger btn-sm mr5' onclick=\"layer.close(getCookie('ChangePath'))\">" + lan.public.close + "</button> <button type='button' id='bt_select' class='btn btn-success btn-sm' >" + lan.bt.path_ok + "</button></div>",
            success: function () {
                $('#btn_back').click(function () {
                    var path = $("#PathPlace").find("span").text();
                    path = bt.rtrim(bt.format_path(path), '/');
                    var back_path = bt.get_file_path(path);
                    _this.get_file_list(back_path, type);
                })
                //选择
                $('#bt_select').on('click', function () {
                    var path = bt.format_path($("#PathPlace").find("span").text());
                    if(type === 'file' && !$('#tbody tr.active').length){
                        layer.msg('Select the file first!',{icon:0})
                        return false;
                    }
                    if ($('#tbody tr').hasClass('active')) {
                        path = $('#tbody tr.active .bt_open_dir').attr('path');
                    }
                    path = bt.rtrim(path, '/');
										if (path.length === 0) {
											path = [$("#PathPlace").find("span").text()]
										}
                    $("#" + id).val(path).change();
                    $("." + id).val(path).change();
                    if(typeof success === "function") success(path)
                    loadT.close();
                })
                var element = $("#" + id),paths = element.val(),defaultPath = $('#defaultPath');
                if (defaultPath.length > 0 && element.parents('.tab-body').length > 0) {
                    paths = defaultPath.text();
                }
                if(default_path){
                    paths = default_path;
                }
                _this.get_file_list(paths, type);
                bt.fixed_table('file-list-table');
            }
        });
        _this.set_cookie('ChangePath', loadT.form);
    //   var paths = $("#" + id).val();
    //   if ($('#defaultPath').length > 0 && $("#" + id).parents('.tab-body').length > 0) {
    //       paths = $('#defaultPath').text();
    //   }
    //   _this.get_file_list(paths, type);

    //   function ActiveDisk() {
    //     var a = $("#PathPlace").find("span").text().substring(0, 1);
    //     switch (a) {
    //         case "C":
    //             $(".path-con-left dd:nth-of-type(1)").css("background", "#eee").siblings().removeAttr("style");
    //             break;
    //         case "D":
    //             $(".path-con-left dd:nth-of-type(2)").css("background", "#eee").siblings().removeAttr("style");
    //             break;
    //         case "E":
    //             $(".path-con-left dd:nth-of-type(3)").css("background", "#eee").siblings().removeAttr("style");
    //             break;
    //         case "F":
    //             $(".path-con-left dd:nth-of-type(4)").css("background", "#eee").siblings().removeAttr("style");
    //             break;
    //         case "G":
    //             $(".path-con-left dd:nth-of-type(5)").css("background", "#eee").siblings().removeAttr("style");
    //             break;
    //         case "H":
    //             $(".path-con-left dd:nth-of-type(6)").css("background", "#eee").siblings().removeAttr("style");
    //             break;
    //         default:
    //             $(".path-con-left dd").removeAttr("style")
    //     }
    //   }
    },
    get_file_list:function(path, type){
			type = type || 'dir'
        var _that = this;
        bt.send('GetDir', 'files/GetDir', { path: path, disk: true }, function(rdata) {
            var d = '',a = '',disk = rdata.DISK;
            if (disk != undefined) {
                for (var f = 0; f < disk.length; f++) {
                    a += "<dd class=\"bt_open_dir size_ellipsis\" title='" + disk[f].path + "' path =\"" + disk[f].path + "\"><span class='glyphicon glyphicon-hdd'></span><span class='text'>" + disk[f].path + "</span></dd>"
                }
                $("#changecomlist").html(a)
            }
            for (var f = 0; f < rdata.DIR.length; f++) {
                var g = rdata.DIR[f].split(";");
                var e = g[0];
                if (e.length > 20) {
                    e = e.substring(0, 20) + "..."
                }
                if (isChineseChar(e)) {
                    if (e.length > 10) {
                        e = e.substring(0, 10) + "..."
                    }
                }
                d += "<tr><td>" + ((type === 'all' || type === 'dir') ? '<input type=\"checkbox\" />' : '') + "</td><td class=\"bt_open_dir\" path =\"" + rdata.PATH + "/" + g[0] + "\" data-type=\"dir\" title='" + g[0] + "'><span class='glyphicon glyphicon-folder-open'></span><span>" + e + "</span></td><td>" + bt.format_data(g[2]) + "</td><td>" + g[3] + "</td><td>" + g[4] + "</td></tr>"
            }

            if (rdata.FILES != null && rdata.FILES != "") {
                for (var f = 0; f < rdata.FILES.length; f++) {
                    var g = rdata.FILES[f].split(";");
                    var e = g[0];
                    if (e.length > 20) {
                        e = e.substring(0, 20) + "..."
                    }
                    if (isChineseChar(e)) {
                        if (e.length > 10) {
                            e = e.substring(0, 10) + "..."
                        }
                    }
                    d += "<tr><td>" + ((type === 'all' || type === 'file') ? '<input type=\"checkbox\" />' : '') + "<td class=\"bt_open_dir\" title='" + g[0] + "' data-type=\"files\" path =\"" + rdata.PATH + "/" + g[0] + "\"><span class='glyphicon glyphicon-file'></span><span>" + e + "</span></td><td>" + bt.format_data(g[2]) + "</td><td>" + g[3] + "</td><td>" + g[4] + "</td></tr>"
                }
            }

            $(".default").hide();
            $(".file-list").show();
            $("#tbody").html(d);
            if (rdata.PATH.substr(rdata.PATH.length - 1, 1) != "/") {
                rdata.PATH += "/"
            }
            $("#PathPlace").find("span").html(rdata.PATH);
            $("#tbody tr").click(function() {
                if ($(this).find('td:eq(0) input').length > 0) {
                    if ($(this).hasClass('active')) {
                        $(this).removeClass('active');
                        $(this).find('td:eq(0) input').prop('checked', false);
                    } else {
                        $(this).find('td:eq(0) input').prop('checked', true);
                        $(this).siblings().find('td:eq(0) input').prop('checked', false);
                        $(this).addClass('active').siblings().removeClass('active');
                    }
                }
            });
      $('#changecomlist dd').click(function(){
        _that.get_file_list($(this).attr('path'), type);
      });
            $('.bt_open_dir span').click(function() {
                if ($(this).parent().data('type') == 'dir') _that.get_file_list($(this).parent().attr('path'), type);
            })
        })
    },
    prompt_confirm: function (title, msg, callback) {
        layer.open({
            type: 1,
            title: title,
            area: "480px",
            closeBtn: 2,
            btn: ['OK', 'Cancel'],
            content: "<div class='bt-form promptDelete pd20'>\
            	<p>" + msg + "</p>\
            	<div class='confirm-info-box'>\
            		<input onpaste='return false;' id='prompt_input_box' type='text' value=''>\
            		<div class='placeholder c9 prompt_input_tips' >If you confirm the operation, enter it manually '<font style='color: red'>" + title + "</font>'</div>\
                    <div style='margin-top:5px;display: none;' class='prompt_input_ps'>The verification code is incorrect. Please enter it manually '<font style='color: red'>" + title + "</font>'</div></div>\
            	</div>",
            success: function () {
                var black_txt_ = $('#prompt_input_box')

                $('.placeholder').click(function () {
                    $(this).hide().siblings('input').focus()
                })
                black_txt_.focus(function () {
                    $('.prompt_input_tips.placeholder').hide()
                })
                black_txt_.blur(function () {
                    black_txt_.val() == '' ? $('.prompt_input_tips.placeholder').show() : $('.prompt_input_tips.placeholder').hide()
                });
                black_txt_.keyup(function () {
                    if (black_txt_.val() == '') {
                        $('.prompt_input_tips.placeholder').show();
                        $('.prompt_input_ps').hide();
                    } else {
                        $('.prompt_input_tips.placeholder').hide();
                    }
                })
            },
            yes: function (layers, index) {
                var result = $("#prompt_input_box").val().trim();
                if (result == title) {
                    layer.close(layers)
                    if (callback) callback()
                } else {
                    $('.prompt_input_ps').show();
                }
            }
        });
    },
    show_confirm: function(title, msg, fun, error) {
        if (error == undefined) {
            error = ""
        }
        var d = Math.round(Math.random() * 9 + 1);
        var c = Math.round(Math.random() * 9 + 1);
        var e = "";
        e = d + c;
        sumtext = d + " + " + c;
        bt.set_cookie("vcodesum", e);
        var mess = layer.open({
            type: 1,
            title: title,
            area: "350px",
            closeBtn: 2,
            shadeClose: true,
            content: "<div class='bt-form webDelete pd20 pb70'><p>" + msg + "</p>" + error + "<div class='vcode'>" + lan.bt.cal_msg + "<span class='text'>" + sumtext + "</span>=<input type='number' id='vcodeResult' value=''></div><div class='bt-form-submit-btn'><button type='button' class='btn btn-danger btn-sm bt-cancel'>" + lan.public.cancel + "</button> <button type='button' id='toSubmit' class='btn btn-success btn-sm' >" + lan.public.ok + "</button></div></div>"
        });
        $("#vcodeResult").focus().keyup(function(a) {
            if (a.keyCode == 13) {
                $("#toSubmit").click()
            }
        });
        $(".bt-cancel").click(function() {
            layer.close(mess);
        });
        $("#toSubmit").click(function() {
            var a = $("#vcodeResult").val().replace(/ /g, "");
            if (a == undefined || a == "") {
                layer.msg(lan.bt.cal_err);
                return
            }
            if (a != bt.get_cookie("vcodesum")) {
                layer.msg(lan.bt.cal_err);
                return
            }
            layer.close(mess);
            fun();
        })
    },
    	/**
	 * @description 计算提示弹窗
	 * @param {Object} config 弹窗对象 {title: 提示标题, msg: 提示内容}
	 * @param {function} callback 回调函数
	 */
	compute_confirm: function (config, callback) {
		var d = Math.round(Math.random() * 9 + 1),
			c = Math.round(Math.random() * 9 + 1),
			t = d + ' + ' + c,
			e = d + c;

		function submit(index, layero) {
			var a = $('#vcodeResult'),
				val = a.val().replace(/ /g, '');
			if (val == undefined || val == '') {
				layer.msg(lan.bt.cal_err);
				return;
			}
			if (val != a.data('value')) {
				layer.msg(lan.bt.cal_err);
				return;
			}
			layer.close(index);
			if (callback) callback();
		}
		layer.open({
			type: 1,
			title: config.title,
			area: '430px',
			closeBtn: 2,
			shadeClose: true,
			btn: [lan['public'].ok, lan['public'].cancel],
			content:
				'<div class="bt-form hint_confirm pd30">\
          <div class="hint_title">\
            <i class="hint-confirm-icon"></i>\
            <div class="hint_con">' +
				config.msg +
				'</div>\
          </div>\
          <div class="vcode">Result：<span class="text">' +
				t +
				'</span>=<input type="number" id="vcodeResult" data-value="' +
				e +
				'" value=""></div>\
      </div>',
			success: function (layero, index) {
				$('#vcodeResult')
					.focus()
					.keyup(function (a) {
						if (a.keyCode == 13) {
							submit(index, layero);
						}
					});
			},
			yes: submit,
		});
	},
    to_login: function() {
        layer.confirm(lan.public_backup.login_expire, { title: lan.public_backup.session_expire, icon: 2, closeBtn: 1, shift: 5 }, function() {
            location.reload();
        });
    },
    do_login: function() {
        bt.confirm({ msg: lan.bt.loginout }, function() {
            window.location.href = "/login?dologin=True"
        })
    },
    send: function(response, module, data, callback, sType) {
        if (sType == undefined) sType = 1;

        module = module.replace('panel_data', 'data');
        sType = 1;
        var str = bt.get_random(16);
        console.time(str);
        if (!response) alert(lan.get('lack_param', ['response']));
        modelTmp = module.split('/')
        if (modelTmp.length < 2) alert(lan.get('lack_param', ['s_module', 'action']));
        if (bt.os == 'Linux' && sType === 0) {
            socket.on(response, function(rdata) {
                socket.removeAllListeners(response);
                var rRet = rdata.data;
                if (rRet.status === -1) {
                    bt.to_login();
                    return;
                }
                console.timeEnd(str);
                if (callback) callback(rRet);
            });
            if (!data) data = {};
            data = bt.linux_format_param(data);
            data['s_response'] = response;
            data['s_module'] = modelTmp[0];
            data['action'] = modelTmp[1];
            socket.emit('panel', data)
        } else {
            data = bt.win_format_param(data);
            var url = '/' + modelTmp[0] + '?action=' + modelTmp[1];
            $.post(url, data, function(rdata) {
                //会话失效时自动跳转到登录页面
                if (typeof(rdata) == 'string') {
                    if ((rdata.indexOf('/static/favicon.ico') != -1 && rdata.indexOf('/static/img/qrCode.png') != -1) || rdata.indexOf('<!DOCTYPE html>') === 0) {
                        window.location.href = "/login"
                        return
                    }
                }

                if (callback) callback(rdata);
            })
        }
    },
    linux_format_param: function(param) {
        if (typeof param == 'string') {
            var data = {};
            arr = param.split('&');
            var reg = /(^[^=]*)=(.*)/;
            for (var i = 0; i < arr.length; i++) {
                var tmp = arr[i].match(reg);
                if (tmp.length >= 3) data[tmp[1]] = tmp[2] == 'undefined' ? '' : tmp[2];
            }
            return data;
        }
        return param;
    },
    win_format_param: function(param) {
        if (typeof data == 'object') {
            var data = '';
            for (var key in param) {
                data += key + '=' + param[key] + '&';
            }
            if (data.length > 0) data = data.substr(0, data.length - 1);
            return data;
        }
        return param;
    },
    msg: function(config) {
			var btnObj = {
				title: config.title ? config.title : false,
				shadeClose: config.shadeClose ? config.shadeClose : true,
				closeBtn: config.closeBtn ? config.closeBtn : 0,
				area: config.area ? config.area : 'auto',
				scrollbar: true,
				shade: 0.3,
			};
			if (!config.hasOwnProperty('time')) config.time = 2000;
			if (typeof config.msg == 'string' && bt.contains(config.msg, 'ERROR')) config.time = 0;
	
			if (config.hasOwnProperty('icon')) {
				if (typeof config.icon == 'boolean') config.icon = config.icon ? 1 : 2;
			} else if (config.hasOwnProperty('status')) {
				config.icon = config.status ? 1 : 2;
				if (!config.status) {
					btnObj.time = 0;
				}
			}
			if (config.icon) btnObj.icon = config.icon;
			btnObj.time = config.time;
			var msg = ''
			if (config.msg) msg += config.msg;
			if (config.msg_error) msg += config.msg_error;
			if (config.msg_solve) msg += config.msg_solve;
	
			layer.msg(msg, btnObj);
    },
    confirm: function(config, callback, callback1) {
        var btnObj = {
            title: config.title ? config.title : false,
            time: config.time ? config.time : 0,
            shadeClose: config.shadeClose ? config.shadeClose : true,
            closeBtn: config.closeBtn ? config.closeBtn : 2,
            scrollbar: true,
            shade: 0.3,
            icon: 3,
						area: config.area ? config.area : 'auto',
            cancel: (config.cancel ? config.cancel : function() {})
        };
        layer.confirm(config.msg, btnObj, function(index) {
            if (callback) callback(index);
        }, function(index) {
            if (callback1) callback1(index);
        });
    },
    load: function(msg) {
        if (!msg) msg = lan.public.the;
        var loadT = layer.msg(msg, { icon: 16, time: 0, shade: [0.3, '#000'] });
        var load = {
            form: loadT,
            close: function() {
                layer.close(load.form);
            }
        }
        return load;
    },
    open: function(config) {
        config.closeBtn = 2;
        var loadT = layer.open(config);
        var load = {
            form: loadT,
            close: function() {
                layer.close(load.form);
            }
        }
        return load;
    },
    closeAll: function() {
        layer.closeAll();
    },
    check_select: function() {
        setTimeout(function() {
            var num = $('input[type="checkbox"].check:checked').length;
            if (num == 1) {
                $('button[batch="true"]').hide();
                $('button[batch="false"]').show();
            } else if (num > 1) {
                $('button[batch="true"]').show();
                $('button[batch="false"]').show();
            } else {
                $('button[batch="true"]').hide();
                $('button[batch="false"]').hide();
            }
        }, 5)
    },
    render_help: function(arr) {
        var html = '<ul class="help-info-text c7">';
        for (var i = 0; i < arr.length; i++) {
            html += '<li>' + arr[i] + '</li>';
        }
        html += '</ul>';
        return html;
    },
    render_ps: function(item) {
        var html = '<p class=\'p1\'>' + item.title + '</p>';
        for (var i = 0; i < item.list.length; i++) {
            html += '<p><span>' + item.list[i].title + '：</span><strong>' + item.list[i].val + '</strong></p>';
        }
        html += '<p style="margin-bottom: 19px; margin-top: 11px; color: #666"></p>';
        return html;
    },
    render_table: function(obj, arr, append) { //渲染表单表格
        var html = '';
        for (var key in arr) {
            html += '<tr><th>' + key + '</th>'
            if (typeof arr[key] != 'object') {
                html += '<td>' + arr[key] + '</td>';
            } else {
                for (var i = 0; i < arr[key].length; i++) {
                    html += '<td>' + arr[key][i] + '</td>';
                }
            }
            html += '</tr>'
        }
        if (append) {
            $('#' + obj).append(html)
        } else {
            $('#' + obj).html(html);
        }
    },

    fixed_table: function(name) {

        $('#' + name).parent().bind('scroll', function() {
            var scrollTop = this.scrollTop;
            $(this).find("thead").css({ "transform": "translateY(" + scrollTop + "px)", "position": "relative", "z-index": "1" });
        });
    },
    render_tab: function(obj, arr) {
        var _obj = $('#' + obj).addClass("tab-nav");
        for (var i = 0; i < arr.length; i++) {
            var item = arr[i];
            var _tab = $('<span ' + (item.on ? 'class="on"' : '') + '>' + item.title + '</span>')
            if (item.callback) {
                _tab.data('callback', item.callback);
                _tab.click(function() {
                    $('#' + obj).find('span').removeClass('on');
                    $(this).addClass('on');
                    var _contents = $('#' + obj).next('.tab-con');
                    _contents.html('');
                    $(this).data('callback')(_contents);
                })
            }
            _obj.append(_tab);
        }
    },
    render_form_line: function(item, bs, form) {
        var clicks = [],
            _html = '',
            _hide = '',
            is_title_css = ' ml0';
        if (!bs) bs = '';
        if (item.title) {
            _html += '<span class="tname">' + item.title + '</span>';
            is_title_css = '';
        }
        _html += "<div class='info-r "+ item.class +" " + is_title_css + (item.hide?'hide':'')  +"'>";

        var _name = item.name;
        var _placeholder = item.placeholder;
        if (item.items && item.type != 'select') {
            for (var x = 0; x < item.items.length; x++) {
                var _obj = item.items[x];
                if (!_name && !_obj.name) {
                    alert(lan.public_backup.name_err);
                    return;
                }
                if (_obj.hide) continue;
                if (_obj.name) _name = _obj.name;
                if (_obj.placeholder) _placeholder = _obj.placeholder;
                if (_obj.title) _html += '<div class="inlineBlock mr5"><span class=" mr5">' + _obj.title + "</span>  ";
                var _add_class = _obj.add_class ? (' '+_obj.add_class) : "";
                switch (_obj.type) {
                    case 'select':
                        var _width = _obj.width ? _obj.width : '100px';
                        _html += '<select ' + (_obj.disabled ? 'disabled' : '') + ' class="bt-input-text mr5 ' + _name + bs + _add_class +'" name="' + _name + '" style="width:' + _width + '">';
                        for (var j = 0; j < _obj.items.length; j++) {
                            _html += '<option ' + (_obj.value == _obj.items[j].value ? 'selected' : '') + ' value="' + _obj.items[j].value + '">' + _obj.items[j].title + '</option>';
                        }
                        _html += '</select>';
                        break;
                    case 'textarea':
                        var _width = _obj.width ? _obj.width : '330px',_height = _obj.height ? _obj.height : '100px';
                        _html += '<textarea class="bt-input-text mr20 ' + _name + bs + _add_class +'" name="' + _name + '" style="width:' + _width + ';height:' + _height + ';line-height:22px">' + (_obj.value ? _obj.value : '') + '</textarea>';
                        if (_placeholder) _html += '<div class="placeholder c9" style="top: 12px; left: 14px; display: block;">' + _placeholder + '</div>';
                        break;
                    case 'button':
                        var _width = _obj.width ? _obj.width : '330px';
                        _html += '<button name=\'' + _name + '\' class="btn btn-success btn-sm mr5 ml5 ' + _name + bs + (_obj.class?_obj.class:'') +'">' + _obj.text + '</button>';
                        break;
                    case 'radio':
                        var _v = _obj.value === true ? 'checked' : '';
                        _html += '<input type="radio" class="' + _name + bs + '" id="' + _name + '" name="' + _name + '"  ' + _v + '><label class="mr20" for="' + _name + '" style="font-weight:normal">' + _obj.text + '</label>'
                        break;
                    case 'radio_group':
                        $.each(_obj.list,function(index,item){
                            var id = _name + '_' + index,_v = _obj.value === item.value ? 'checked' : '';
                            _html += '<div class="radio_item"><input type="radio" class="' + _name + bs + '" id="' + id + '" name="' + _name + '"  ' + _v + ' value="'+  item.value +'"><label class="mr20" for="' + id + '" style="font-weight:normal">' + item.text + '</label></div>'
                        });
                        break;
                    case 'checkbox':
                        var _v = _obj.value === true ? 'checked' : '';
                        _html += '<input type="checkbox" class="' + _name + bs + '" id="' + _name + '" name="' + _name + '" '+ (_obj.disabled?'disabled':'') +'  ' + _v + '><label class="mr20" for="' + _name + '" style="font-weight:normal">' + _obj.text + '</label>';
                        break;
                    case 'number':
                        var _width = _obj.width ? _obj.width : '330px';
                        _html += "<input name='" + _name + "' " + (_obj.disabled ? 'disabled' : '') + " class='bt-input-text mr5 " + _name + bs + _add_class +"' " + (_placeholder ? ' placeholder="' + _placeholder + '"' : "") + " type='number' style='width:" + _width + "' value='" + (_obj.value ? _obj.value : '0') + "' />";
                        _html += _obj.unit ? _obj.unit : '';
                        break;
                    case 'password':
                        var _width = _obj.width ? _obj.width : '330px';
                        _html += "<input name='" + _name + "' " + (_obj.disabled ? 'disabled' : '') + " class='bt-input-text mr5 " + _name + bs + "' " + (_placeholder ? ' placeholder="' + _placeholder + '"' : "") + " type='password' style='width:" + _width + "' value='" + (_obj.value ? _obj.value : '') + "' />";
                        break;
                    case 'div':
                    	var _width = _obj.width ? _obj.width : '330px',_height = _obj.height ? _obj.height : '100px';
                        _html += '<div class="bt-input-text ace_config_editor_scroll mr20 ' + _name + bs + _add_class +'" name="' + _name + '" style="width:' + _width + ';height:' + _height + ';line-height:22px">' + (_obj.value ? _obj.value : '') + '</div>';
                        if (_placeholder) _html += '<div class="placeholder c9" style="top: 15px; left: 15px; display: block;">' + _placeholder + '</div>';
                        break;
                    case 'switch':
                        _html += '<div style="display: inline-block;vertical-align: middle;">\
                            <input type="checkbox" id="' + _name + '" ' + (_obj.value==true?'checked':'') + ' class="btswitch btswitch-ios">\
                            <label class="btswitch-btn" for="' + _name + '" style="margin-top:5px;"></label>\
                        </div>';
                        break;
                    case 'html':
                        _html += _obj.html;
                        break;
                    default:
                        var _width = _obj.width ? _obj.width : '330px';
                        _html += "<input name='" + _name + "' " + (_obj.disabled ? 'disabled' : '') + " class='bt-input-text mr5 " + _name + bs + _add_class +"' " + (_placeholder ? ' placeholder="' + _placeholder + '"' : "") + " type='text' style='width:" + _width + "' value='" + (_obj.value ? _obj.value : '') + "' />";
                        break;
                }
                if (_obj.title) _html += '</div>';
                if (_obj.callback) clicks.push({ bind: _name + bs, callback: _obj.callback });
                if (_obj.event) {
                    _html += '<span data-id="' + _name + bs + '" class="glyphicon cursor mr5 ' + _obj.event.css + ' icon_' + _name + bs + '" ></span>';
                    if (_obj.event.callback) clicks.push({ bind: 'icon_' + _name + bs, callback: _obj.event.callback });
                }
                if (_obj.ps) _html += " <span class='c9 mt10'>" + _obj.ps + "</span>";
                if (_obj.ps_help) _html += "<span class='bt-ico-ask "+_obj.name+"_help' tip='"+_obj.ps_help+"'>?</span>";
            }
            if (item.ps) _html += " <span class='c9 mt10'>" + item.ps + "</span>";
            if (item.ps_help) _html += "<span class='bt-ico-ask "+item.name+"_help' tip='"+item.ps_help+"'>?</span>";
        } else {
            switch (item.type) {
                case 'select':
                    var _width = item.width ? item.width : '100px';
                    _html += '<select ' + (item.disabled ? 'disabled' : '') + ' class="bt-input-text mr5 ' + _name + bs + '" name="' + _name + '" style="width:' + _width + '">';
                    for (var j = 0; j < item.items.length; j++) {
                        _html += '<option ' + (item.value == item.items[j].value ? 'selected' : '') + ' value="' + item.items[j].value + '">' + item.items[j].title + '</option>';
                    }
                    _html += '</select>';
                    break;
                case 'button':
                    var _width = item.width ? item.width : '330px';
                    _html += '<button name=\'' + _name + '\' class="btn btn-success btn-sm mr5 ml5 ' + _name + bs + '">' + item.text + '</button>';
                    break;
                case 'number':
                    var _width = item.width ? item.width : '330px';
                    _html += "<input name='" + item.name + "' " + (item.disabled ? 'disabled' : '') + " class='bt-input-text mr5 " + _name + bs + "' " + (_placeholder ? ' placeholder="' + _placeholder + '"' : "") + " type='number' style='width:" + _width + "' value='" + (item.value ? item.value : '0') + "' />";
                    break;
                case 'checkbox':
                    var _v = item.value === true ? 'checked' : ''
                    _html += '<input type="checkbox" class="' + _name + '" id="' + _name + '" name="' + _name + '"  ' + _v + '><label class="mr20" for="' + _name + '" style="font-weight:normal">' + item.text + '</label>'
                    break;
                case 'password':
                    var _width = item.width ? item.width : '330px';
                    _html += "<input name='" + _name + "' " + (item.disabled ? 'disabled' : '') + " class='bt-input-text mr5 " + _name + bs + "' " + (_placeholder ? ' placeholder="' + _placeholder + '"' : "") + " type='password' style='width:" + _width + "' value='" + (item.value ? item.value : '') + "' />";
                    break;
                case 'textarea':
                    var _width = item.width ? item.width : '330px';
                    var _height = item.height ? item.height : '100px';
                    _html += '<textarea class="bt-input-text mr20 ' + _name + bs + '"  ' + (item.disabled ? 'disabled' : '')+'  name="' + _name + '" style="width:' + _width + ';height:' + _height + ';line-height:22px">' + (item.value ? item.value : '') + '</textarea>';
                    if (_placeholder) _html += '<div class="placeholder c9" style="top: 15px; left: 15px; display: block;">' + _placeholder + '</div>';
                    break;
                default:
                    var _width = item.width ? item.width : '330px';

                    _html += "<input name='" + item.name + "' " + (item.disabled ? 'disabled' : '') + " class='bt-input-text mr5 " + _name + bs + "' " + (_placeholder ? ' placeholder="' + _placeholder + '"' : "") + " type='text' style='width:" + _width + "' value='" + (item.value ? item.value : '') + "' />";
                    break;
            }
            if (item.callback) clicks.push({ bind: _name + bs, callback: item.callback });
            if (item.ps) _html += " <span class='c9 mt10 mr5'>" + item.ps + "</span>";
            if (item.ps_help) _html += "<span class='bt-ico-ask "+item.name+"_help' tip='"+item.ps_help+"'>?</span>";
        }
        _html += '</div>';
        if (!item.class) item.class = '';
        if (item.hide) _hide = 'style="display:none;"'
        _html = '<div class="line ' + item.class + '" ' + _hide + '>' + _html + '</div>'

        if (form) {
            form.append(_html)
            bt.render_clicks(clicks)
        }
        return { html: _html, clicks: clicks, data: item };
    },
    render_form: function(data, callback) {
        if (data) {
            var bs = '_' + bt.get_random(6);
            var _form = $("<div data-id='form" + bs + "' class='bt-form bt-form pd20 pb70 " + (data.class ? data.class : '') + "'></div>");
            var _lines = data.list;
            var clicks = [];
            for (var i = 0; i < _lines.length; i++) {
                var _obj = _lines[i]
                if (_obj.hasOwnProperty("html")) {
                    _form.append(_obj.html)
                } else {
                    var rRet = bt.render_form_line(_obj, bs);
                    for (var s = 0; s < rRet.clicks.length; s++) clicks.push(rRet.clicks[s]);
                    _form.append(rRet.html);
                }
            }

            var _btn_html = '';
            for (var i = 0; i < data.btns.length; i++) {
                var item = data.btns[i];
                var css = item.css ? item.css : 'btn-danger';
                _btn_html += "<button type='button' class='btn btn-sm " + css + " " + item.name + bs + "' >" + item.title + "</button>";
                clicks.push({ bind: item.name + bs, callback: item.callback });
            }
            _form.append("<div class='bt-form-submit-btn'>" + _btn_html + "</div>");
            var loadOpen = bt.open({
                type: 1,
                skin: data.skin,
                area: data.area,
                title: data.title,
                closeBtn: 2,
                content: _form.prop("outerHTML"),
                end: data.end ? data.end : false,
                success:function(){
                    if (data.success) data.success()
                }
            })
            setTimeout(function() {
                bt.render_clicks(clicks, loadOpen, callback);
            }, 100)
        }
        return bs;
    },
    render_clicks: function(clicks, loadOpen, callback) {
        for (var i = 0; i < clicks.length; i++) {
            var obj = clicks[i];

            var btn = $('.' + obj.bind);
            btn.data('item', obj);
            btn.data('load', loadOpen);
            btn.data('callback', callback);

            switch (btn.prop("tagName")) {
                case 'SPAN':
                    btn.click(function() {
                        var _obj = $(this).data('item');
                        _obj.callback($(this).attr('data-id'));
                    })
                    break;
                case 'SELECT':
                    btn.change(function() {
                        var _obj = $(this).data('item');
                        _obj.callback($(this));
                    })
                    break;
                case 'TEXTAREA':
                case 'INPUT':
                case 'BUTTON':

                    if (btn.prop("tagName") == 'BUTTON' || btn.attr("type") == 'checkbox') {
                        btn.click(function() {
                            var _obj = $(this).data('item');
                            var load = $(this).data('load');
                            var _callback = $(this).data('callback');
                            var parent = $(this).parents('.bt-form');

                            if (_obj.callback) {

                                var data = {};
                                parent.find('*').each(function(index, _this) {
                                    var _name = $(_this).attr('name');

                                    if (_name) {
                                        if ($(_this).attr('type') == 'checkbox' || $(_this).attr('type') == 'radio') {
                                            data[_name] = $(_this).prop('checked');
                                        } else {
                                            data[_name] = $(_this).val();
                                        }
                                    }
                                })
                                _obj.callback(data, load, function(rdata) {
                                    if (_callback) _callback(rdata);
                                });
                            } else {
                                load.close();
                            }
                        })
                    } else {
                        if (btn.attr("type") == 'radio') {
                            btn.click(function() {
                                var _obj = $(this).data('item');
                                _obj.callback($(this))
                            })
                        } else {
                            btn.on('input', function() {
                                var _obj = $(this).data('item');
                                _obj.callback($(this));
                            })
                        }
                    }
                    break;
            }
        }
    },
    render: function(obj) //columns 行
        {
            if (obj.columns) {
                var checks = {};
                $(obj.table).html('');
                var thead = '<thead><tr>';
                for (var h = 0; h < obj.columns.length; h++) {
                    var item = obj.columns[h];
                    if (item) {
                        thead += '<th';
                        if (item.width) thead += ' width="' + item.width + '" ';
                        if (item.align || item.sort) {
                            thead += ' style="';
                            if (item.align) thead += 'text-align:' + item.align + ';';
                            if (item.sort) thead += item.sort ? 'cursor: pointer;' : '';
                            thead += '"';
                        }
                        if (item.type == 'checkbox') {
                            thead += '><input  class="check"  onclick="bt.check_select();" type="checkbox">';
                        } else {
                            thead += '>' + item.title;
                        }
                        if (item.sort) {
                            checks[item.field] = item.sort;
                            thead += ' <span data-id="' + item.field + '" class="glyphicon glyphicon-triangle-top" style="margin-left:5px;color:#bbb"></span>';
                        }
                        if (item.help) thead += '<a href="' + item.help + '" class="bt-ico-ask" target="_blank" title="' + lan.public_backup.click_detail + '">?</a>';

                        thead += '</th>';
                    }
                }
                thead += '</tr></thead>';
                var _tab = $(obj.table).append(thead);
                if (obj.data.length > 0) {
                    for (var i = 0; i < obj.data.length; i++) {
                        var val = obj.data[i];
                        var tr = $('<tr></tr>');
                        for (var h = 0; h < obj.columns.length; h++) {
                            var item = obj.columns[h];
                            if (item) {
                                var _val = val[item.field];
                                if (typeof _val == 'string') _val = _val.replace(/\\/g, '');
                                if (item.hasOwnProperty('templet')) _val = item.templet(val);
                                if (item.type == 'checkbox') _val = '<input value=' + val[item.field] + '  class="check" onclick="bt.check_select();" type="checkbox">';
                                var td = '<td ';
                                if (item.align) {
                                    td += 'style="';
                                    if (item.align) td += 'text-align:' + item.align;
                                    td += '"';
                                }
                                if (item.index) td += 'data-index="' + i + '" '
                                td += '>';
                                tr.append(td + _val + '</td>');
                                tr.data('item', val);
                                _tab.append(tr);
                            }
                        }
                    }
                } else {
                    _tab.append("<tr><td colspan='" + obj.columns.length + "'>" + obj.empty? obj.empty:lan.bt.no_data + "</td></tr>");
                }
                $(obj.table).find('.check').click(function() {
                    var checked = $(this).prop('checked');
                    if ($(this).parent().prop('tagName') == 'TH') {
                        $('.check').prop('checked', checked ? 'checked' : '');
                    }
                })
                var asc = 'glyphicon-triangle-top';
                var desc = 'glyphicon-triangle-bottom';

                var orderby = bt.get_cookie('order');
                if (orderby != undefined) {
                    var arrys = orderby.split(' ')
                    if (arrys.length == 2) {
                        if (arrys[1] == 'asc') {
                            $(obj.table).find('th span[data-id="' + arrys[0] + '"]').removeClass(desc).addClass(asc);
                        } else {
                            $(obj.table).find('th span[data-id="' + arrys[0] + '"]').removeClass(asc).addClass(desc);
                        }
                    }
                }

                $(obj.table).find('th').data('checks', checks).click(function() {
                    var _th = $(this);
                    var _checks = _th.data('checks');
                    var _span = _th.find('span');
                    if (_span.length > 0) {
                        var or = _span.attr('data-id');
                        if (_span.hasClass(asc)) {
                            bt.set_cookie('order', or + ' desc');
                            $(obj.table).find('th span[data-id="' + or + '"]').removeClass(asc).addClass(desc);
                            _checks[or]();

                        } else if (_span.hasClass(desc)) {
                            bt.set_cookie('order', or + ' asc');
                            $(obj.table).find('th span[data-id="' + arrys[0] + '"]').removeClass(desc).addClass(asc);
                            _checks[or]();
                        }
                    }
                })
            }
            return _tab;
        },
    // ACE编辑配置文件
    aceEditor: function(obj) {
        var aEditor = {
                ACE: ace.edit(obj.el, {
                    theme: obj.theme ? obj.theme : "ace/theme/chrome", // 主题
                    mode: "ace/mode/" + (obj.mode || 'nginx'), // 语言类型
                    wrap: true,
                    showInvisibles: false,
                    showPrintMargin: false,
                    showFoldWidgets: false,
                    useSoftTabs: true,
                    tabSize: 2,
                    showPrintMargin: false,
                    readOnly: false
                }),
                path: obj.path,
                content: '',
                saveCallback: obj.saveCallback
            },
            _this = this;
        $('#' + obj.el).css('fontSize', '12px');
        aEditor.ACE.commands.addCommand({
            name: '保存文件',
            bindKey: { win: 'Ctrl-S', mac: 'Command-S' },
            exec: function(editor) {
                _this.saveEditor(aEditor, aEditor.saveCallback);
            },
            readOnly: false // 如果不需要使用只读模式，这里设置false
        });
        if (obj.path != undefined) {
            var loadT = layer.msg(lan.soft.get_config, { icon: 16, time: 0, shade: [0.3, '#000'] })
            bt.send('GetFileBody', 'files/GetFileBody', { path: obj.path }, function(res) {
                layer.close(loadT);
                if (!res.status) {
                    bt.msg(res);
                    return false;
                }
                aEditor.ACE.setValue(res.data); //设置配置文件内容
                aEditor.ACE.moveCursorTo(0, 0); //设置文件光标位置
                aEditor.ACE.resize();
            });
        } else if (obj.content != undefined) {
            aEditor.ACE.setValue(obj.content);
            aEditor.ACE.moveCursorTo(0, 0); //设置文件光标位置
            aEditor.ACE.resize();
        }
        return aEditor;
    },
    // 保存编辑器文件
    saveEditor: function(ace) {
        if (!ace.saveCallback) {
            var loadT = bt.load(lan.soft.the_save);
            bt.send('SaveFileBody', 'files/SaveFileBody', { data: ace.ACE.getValue(), path: ace.path, encoding: 'utf-8' }, function(rdata) {
                loadT.close();
                bt.msg(rdata);
            });
        } else {
            ace.saveCallback(ace.ACE.getValue());
        }
    },
    /**
     * @description 遍历数组和对象
     * @param {Array|Object} obj 遍历数组|对象
     * @param {Function} fn 遍历对象或数组
     * @return 当前对象
     */
    each: function (obj, fn) {
        var key, that = this;
        if (typeof fn !== 'function') return that;
        obj = obj || [];
        if (obj.constructor === Object) {
            for (key in obj) {
                if (fn.call(obj[key], key, obj[key])) break;
            }
        } else {
            for (key = 0; key < obj.length; key++) {
                if (fn.call(obj[key], key, obj[key])) break;
            }
        }
        return that;
    },
	/**
	 * @description 普通提示弹窗
	 * @param {Object} config 弹窗对象 {title:标题, msg:提示内容}
	 * @param {function} callback 确认回调函数
	 * @param {function} callback1 取消回调函数
	 */
	simple_confirm: function (config, callback, callback1) {
		layer.open({
			type: 1,
			title: config.title,
			area: '430px',
			closeBtn: 2,
			shadeClose: false,
			btn: [lan['public'].ok, lan['public'].cancel],
			content:
				'<div class="bt-form hint_confirm pd30">\
        <div class="hint_title">\
          <i class="hint-confirm-icon"></i>\
          <div class="hint_con">' +
				config.msg +
				'</div>\
        </div>\
      </div>',
			yes: function (index, layero) {
				if (callback && typeof callback(index) === 'undefined') layer.close(index);
			},
			btn2: function (index) {
				//取消返回回调
				if (callback1 && typeof callback1(index) === 'undefined') layer.close(index);
			},
			cancel: function (index) {
				//取消返回回调
				if (callback1 && typeof callback1(index) === 'undefined') layer.close(index);
			}
		});
	},
/**
	 * @description 需求反馈弹窗
	 * @param {Object} param 配置对象 {title:标题, placeholder:反馈问题pl(可带标签),recover:input框下方提示语, key:反馈问题key, proType:产品类型}
	 */
	openFeedback: function (param) {
		// 需求反馈
		var openFeed = bt_tools.open({
			area:['570px','400px'],
			btn:false,
			content:'<div id="feedback">\
			<div class="nps_survey_banner">\
			<span class="Ftitle"> <i></i> <span style="vertical-align:4px;">'+param.title+'</span> </span>\
		</div>\
		<div style="padding: 25px 0 0 40px">\
			<div class="flex flex-col items-center">\
				<div id="feedForm"></div>\
			</div>\
		</div>\
		</div>',
			success:function(that){
				var id = "x66ed9v07MjVjYjczNTUyMDE0Le8BEdl"
				bt_tools.send({url:'/config?action=get_nps_new',data:{product_type:param.proType}},function(ress){
					//请求回调
					console.log(ress);
					if(ress.res){
						id = ress.res[0].id
					}
				},{load:'Loading...',verify:false})
				//打开弹窗后执行的事件
				that.find('.layui-layer-title').remove()
				bt_tools.form({
					el:'#feedForm',
					form:[
						{
							group: {
								type: 'textarea',
								name: 'feed',
								style: {
									'width': '500px',
									'min-width': '500px',
									'min-height': '130px',
									'line-height': '22px',
									'padding-top': '10px',
									'resize': 'none'
								},
								tips: { //使用hover的方式显示提示
									text: param.placeholder,
									style: { top: '126px', left: '50px' },
								},
							}
						},
						{
							group:{
								name: 'tips',
								type: 'other',
								boxcontent:'<div style="color:#20a53a;margin-left:-5px;">'+param.recover+'</div>'
							}
						},
						{
							group: {
								type: 'button',
								size: '',
								name: 'submitForm',
								class:'feedBtn',
								style:'margin:10px auto 0;padding:6px 40px;',
								title: 'Submit',
								event: function (formData, element, that) {
									// 触发submit
									if(formData.feed == '') {
										return bt.msg({status:false,msg:'Please fill in the feedback'})
									}
									var config = {}
									config[id] = formData.feed
									bt_tools.send({url:'config?action=write_nps_new',data:{questions:JSON.stringify(config),rate:0,product_type:param.proType}},function(ress){
										if(ress.status){
											openFeed.close()
											layer.open({
												title: false,
												btn: false,
												shadeClose: true,
												shade:0.1,
												closeBtn: 0,
												skin:'qa_thank_dialog',
												area: '230px',
												content: '<div class="qa_thank_box" style="background-color:#F1F9F3;text-align: center;padding: 20px 0;"><img src="/static/img/feedback/QA_like.png" style="width: 55px;"><p style="margin-top: 15px;">Thank you for your participation!</p></div>',
												success: function (layero,index) {
													$(layero).find('.layui-layer-content').css({'padding': '0','border-radius': '5px'})
													$(layero).css({'border-radius': '5px','min-width': '230px'})

													setTimeout(function(){layer.close(index)},3000)
												}
											})
										}
									},'submit feedback')

								}
							}
						}
					]
				})
			},
			yes:function(){
				//点击确定时,如果btn:false,当前事件将无法使用
			},
			cancel: function () {
				//点击右上角关闭时,如果btn:false,当前事件将无法使用
			}
		})
},
};



bt.pub = {
    get_data: function(data, callback, hide) {
        if (!hide) var loading = bt.load(lan.public.the);
        bt.send('getData', 'data/getData', data, function(rdata) {
            if (loading) loading.close();
            if (callback) callback(rdata);
        })
    },
    set_data_by_key: function(tab, key, obj) {
        var _span = $(obj);
        var _input = $("<input class='baktext' value='" + _span.text() + "' type='text' placeholder='" + lan.ftp.ps + "' />");
        _span.hide().after(_input);
        _input.focus();
        _input.blur(function() {
            var item = $(this).parents('tr').data('item');
            var _txt = $(this);
            var data = { table: tab, id: item.id };
            data[key] = _txt.val()
            bt.pub.set_data_ps(data, function(rdata) {
                if (rdata.status) {
                    _span.text(_txt.val());
                    _span.show();
                    _txt.remove();
                }
            })
        })
        _input.keyup(function() {
            if (event.keyCode == 13) {
                _input.trigger("blur");
            }
        })
    },
    set_data_ps: function(data, callback) {
        bt.send('setPs', 'data/setPs', data, function(rdata) {
            if (callback) callback(rdata);
        })
    },
    set_server_status: function(serverName, type) {
        if (bt.contains(serverName, 'php-')) {
            serverName = "php-fpm-" + serverName.replace('php-', '').replace('.', '');
        }
        if (serverName == 'pureftpd') serverName = 'pure-ftpd';
        if (serverName == 'mysql') serverName = 'mysqld';
        serverName = serverName.replace('_soft', '');
        var data = "name=" + serverName + "&type=" + type;
        var msg = lan.bt[type];
        var typeName = '';
        switch (type) {
            case 'stop':
                typeName = lan.public_backup.stop;
                break;
            case 'restart':
                typeName = lan.public_backup.restart;
                break;
            case 'reload':
                typeName = lan.public_backup.reload;
                break;
        }
        bt.confirm({ msg: lan.get('service_confirm', [msg, serverName]), title: typeName + serverName + lan.public_backup.server }, function() {
            var load = bt.load(lan.get('service_the', [msg, serverName]))
            bt.send('system', 'system/ServiceAdmin', data, function(rdata) {
                load.close();
                var f = rdata.status ? lan.get('service_ok', [serverName, msg]) : lan.get('service_err', [serverName, msg]);
                bt.msg({ msg: f, icon: rdata.status })

                if (type != "reload" && rdata.status) {
                    setTimeout(function() {
                        window.location.reload()
                    }, 1000)
                }
                if (!rdata.status) {
                    bt.msg(rdata);
                }
            })
        })
    },
		set_ftp_logs: function (type) {
			var serverName = 'pure-ftpd';
			var data = 'exec_name=' + type;
			var typeName = 'enabling ';
			var TypeName = 'Enabling ';
			switch (type) {
				case 'stop':
					typeName = 'disabling ';
					TypeName = 'Disabling ';
					break;
			}
			var status = type == 'stop' ? false : true;
			layer.confirm(
				'After '+typeName + 'pure-ftpd Logs management,' + (status ? 'all login and operation records of FTP users will be recorded.' : 'it will no longer be possible to record all login and operation records of FTP users. ') + ' Do you want to proceed?',
				{
					title: TypeName + serverName + ' logs management',
					closeBtn: 2,
					icon: 3,
					cancel: function () {
						$('#isFtplog').prop('checked', !status);
					},
				},
				function () {
					var load = bt.load(TypeName + 'Pure-FTPd logs management, please wait...');
					bt.send('ftp', 'ftp/set_ftp_logs', data, function (rdata) {
						load.close();
						bt.msg(rdata);
						$('.bt-soft-menu p').eq(3).click();
					});
				},
				function () {
					$('#isFtplog').prop('checked', !status);
				}
			);
		},
		get_ftp_logs: function (callback) {
			bt.send('ftp', 'ftp/set_ftp_logs', { exec_name: 'getlog' }, function (res) {
				var _status = res.msg === 'start' ? true : false;
				if (callback) callback(_status);
			});
		},
    set_server_status_by: function(data, callback) {
        bt.send('system', 'system/ServiceAdmin', data, function(rdata) {
            if (callback) callback(rdata)
        })
    },
    get_task_count: function(callback) {
        bt.send('GetTaskCount', 'ajax/GetTaskCount', {}, function(rdata) {
            $(".task").text(rdata);
            if(callback) callback(rdata);
        })
    },
    check_install: function(callback) {
        bt.send('CheckInstalled', 'ajax/CheckInstalled', {}, function(rdata) {
            if (callback) callback(rdata);
        })
    },
    get_user_info: function(callback) {
        var loading = bt.load();
        bt.send('GetUserInfo', 'ssl/GetUserInfo', {}, function(rdata) {
            loading.close();
            if (callback) callback(rdata);
        })
    },
    show_hide_pass: function(obj) {
        var a = "glyphicon-eye-open";
        var b = "glyphicon-eye-close";

        if ($(obj).hasClass(a)) {
            $(obj).removeClass(a).addClass(b);
            $(obj).prev().text($(obj).prev().attr('data-pw'))
        } else {
            $(obj).removeClass(b).addClass(a);
            $(obj).prev().text('**********');
        }
    },
    copy_pass: function(password) {
        var clipboard = new ClipboardJS('#bt_copys');
        clipboard.on('success', function(e) {
            bt.msg({ msg: lan.public_backup.cp_success, icon: 1 });
        });

        clipboard.on('error', function(e) {
            bt.msg({ msg: lan.public_backup.cp_fail, icon: 2 });
        });
        $("#bt_copys").attr('data-clipboard-text', password);
        $("#bt_copys").click();
    },
    login_btname: function(username, password, callback) {
        var loadT = bt.load(lan.config.token_get);
        bt.send('GetToken', 'ssl/GetToken', "username=" + username + "&password=" + password, function(rdata) {
            loadT.close();
            bt.msg(rdata);
            if (rdata.status) {
                if (callback) callback(rdata)
            }
        })
    },
    bind_btname: function(callback) {
        layer.open({
            type: 1,
            title: lan.public_backup.bind_bt_account,
            area: ['420px', '360px'],
            closeBtn: 2,
            shadeClose: false,
            content: '<div class="libLogin pd20" ><div class="bt-form text-center"><div class="line mb15"><h3 class="c2 f16 text-center mtb20">' + lan.public_backup.bind_bt_account + '</h3></div><div class="line"><input class="bt-input-text" name="username2" type="text" placeholder="' + lan.public_backup.mobile_phone_or_email + '" id="p1"></div><div class="line"><input autocomplete="new-password" class="bt-input-text" type="password" name="password2"  placeholder="' + lan.public_backup.pass + '" id="p2"></div><div class="line"><input class="login-button" value="' + lan.public_backup.login + '" type="button" ></div><p class="text-right"><a class="btlink" href="https://brandnew.aapanel.com/user_admin/login" target="_blank">' + lan.public_backup.no_account + '</a></p></div></div>'
        });
        setTimeout(function() {
            $('.login-button').click(function() {
                p1 = $("#p1").val();
                p2 = $("#p2").val();
                var loadT = bt.load(lan.config.token_get);
                bt.send('GetToken', 'ssl/GetToken', "username=" + p1 + "&password=" + p2, function(rdata) {
                    loadT.close();
                    bt.msg(rdata);
                    if (rdata.status) {
                        if (callback) {
                            layer.closeAll();
                            callback(rdata)
                        } else {
                            window.location.reload();
                        }
                        $("input[name='btusername']").val(p1);
                    }
                })
            })
        }, 100)
    },
    unbind_bt: function() {
        var name = $("input[name='btusername']").val();
        bt.confirm({ msg: lan.config.binding_un_msg, title: lan.config.binding_un_title }, function() {
            bt.send('DelToken', 'ssl/DelToken', {}, function(rdata) {
                bt.msg(rdata);
                $("input[name='btusername']").val('');
            })
        })
    },
    get_menm: function(callback) {
        var loading = bt.load();
        bt.send('GetMemInfo', 'system/GetMemInfo', {}, function(rdata) {
            loading.close();
            if (callback) callback(rdata);
        })
    },
    on_edit_file: function(type, fileName) {
        if (type != 0) {
            var l = $("#PathPlace input").val();
            var body = encodeURIComponent($("#textBody").val());
            var encoding = $("select[name=encoding]").val();
            var loadT = bt.load(lan.bt.save_file);
            bt.send('SaveFileBody', 'files/SaveFileBody', "data=" + body + "&path=" + fileName + "&encoding=" + encoding, function(rdata) {
                if (type == 1) loadT.close();
                bt.msg(rdata);
            })
            return;
        }
        var loading = bt.load(lan.bt.read_file);
        ext = bt.get_file_ext(fileName);
        doctype = '';
        switch (ext) {
            case "html":
                var mixedMode = { name: "htmlmixed", scriptTypes: [{ matches: /\/x-handlebars-template|\/x-mustache/i, mode: null }, { matches: /(text|application)\/(x-)?vb(a|script)/i, mode: "vbscript" }] };
                doctype = mixedMode;
                break;
            case "htm":
                var mixedMode = { name: "htmlmixed", scriptTypes: [{ matches: /\/x-handlebars-template|\/x-mustache/i, mode: null }, { matches: /(text|application)\/(x-)?vb(a|script)/i, mode: "vbscript" }] };
                doctype = mixedMode;
                break;
            case "js":
                doctype = "text/javascript";
                break;
            case "json":
                doctype = "application/ld+json";
                break;
            case "css":
                doctype = "text/css";
                break;
            case "php":
                doctype = "application/x-httpd-php";
                break;
            case "tpl":
                doctype = "application/x-httpd-php";
                break;
            case "xml":
                doctype = "application/xml";
                break;
            case "sql":
                doctype = "text/x-sql";
                break;
            case "conf":
                doctype = "text/x-nginx-conf";
                break;
            default:
                var mixedMode = { name: "htmlmixed", scriptTypes: [{ matches: /\/x-handlebars-template|\/x-mustache/i, mode: null }, { matches: /(text|application)\/(x-)?vb(a|script)/i, mode: "vbscript" }] };
                doctype = mixedMode;
                break;
        }
        bt.send('GetFileBody', 'files/GetFileBody', 'path=' + fileName, function(rdata) {
            if (!rdata.status) {
                bt.msg({ msg: rdata.msg, icon: 5 });
                return;
            }
            loading.close();
            var u = ["utf-8", "GBK", "GB2312", "BIG5"];
            var n = "";
            var m = "";
            var o = "";
            for (var p = 0; p < u.length; p++) {
                m = rdata.encoding == u[p] ? "selected" : "";
                n += '<option value="' + u[p] + '" ' + m + ">" + u[p] + "</option>"
            }
            var r = bt.open({
                type: 1,
                shift: 5,
                closeBtn: 1,
                //maxmin: true,
                area: ["90%", "90%"],
                shade: false,
                title: lan.bt.edit_title + "[" + fileName + "]",
                content: '<form class="bt-form pd20 pb70"><div class="line"><p style="color:red;margin-bottom:10px">' + lan.bt.edit_ps +
                    '		<select class="bt-input-text" name="encoding" style="width: 74px;position: absolute;top: 31px;right: 19px;height: 22px;z-index: 9999;border-radius: 0;">' +
                    n + '</select></p><textarea class="mCustomScrollbar bt-input-text" id="textBody" style="width:100%;margin:0 auto;line-height: 1.8;position: relative;top: 10px;" value="" /></div><div class="bt-form-submit-btn" style="position:absolute; bottom:0; width:100%"><button type="button" class="btn btn-danger btn-sm btn-editor-close">' + lan.public.close + '</button><button id="OnlineEditFileBtn" type="button" class="btn btn-success btn-sm">' + lan.public.save + '</button></div></form>'
            })
            $("#textBody").text(rdata.data);
            var q = $(window).height() * 0.9;
            $("#textBody").height(q - 160);
            var t = CodeMirror.fromTextArea(document.getElementById("textBody"), {
                extraKeys: {
                    "Ctrl-F": "findPersistent",
                    "Ctrl-H": "replaceAll",
                    "Ctrl-S": function() {
                        $("#textBody").text(t.getValue());
                        bt.pub.on_edit_file(2, fileName)
                    }
                },
                mode: doctype,
                lineNumbers: true,
                matchBrackets: true,
                matchtags: true,
                autoMatchParens: true
            });
            t.focus();
            t.setSize("auto", q - 150);
            $("#OnlineEditFileBtn").click(function() {
                $("#textBody").text(t.getValue());
                bt.pub.on_edit_file(1, fileName);
            });
            $(".btn-editor-close").click(function() {
                r.close();
            });
        })
    }
};

bt.index = {
    rec_install: function() {
        bt.send('GetSoftList', 'ajax/GetSoftList', {}, function(l) {
            var c = "";
            var g = "";
            var e = "";
            for (var h = 0; h < l.length; h++) {
                if (l[h].name == "Tomcat") {
                    continue
                }
                var o = "";
                var m = "<input id='data_" + l[h].name + "' data-info='" + l[h].name + " " + l[h].versions[0].version + "' type='checkbox' "+ (l[h].name == 'DNS-Server' || l[h].name == 'Mail-Server' ? '' : 'checked') +">";
                for (var b = 0; b < l[h].versions.length; b++) {
                    var d = "";
                    if ((l[h].name == "PHP" && (l[h].versions[b].version == "7.4" || l[h].versions[b].version == "7.4")) || (l[h].name == "MySQL" && l[h].versions[b].version == "5.7") || (l[h].name == "phpMyAdmin" && l[h].versions[b].version == "5.0")) {
                        d = "selected";
                        m = "<input id='data_" + l[h].name + "' data-info='" + l[h].name + " " + l[h].versions[b].version + "' type='checkbox' checked>"
                    }
                    o += "<option value='" + l[h].versions[b].version + "' " + d + ">" + l[h].name + " " + l[h].versions[b].version + "</option>"
                }
                var f = "<li><span class='ico'><img src='/static/img/" + l[h].name.toLowerCase() + ".png'></span><span class='name'><select id='select_" + l[h].name + "' class='sl-s-info'>" + o + "</select></span><span class='pull-right'>" + m + "</span></li>";
                if (l[h].name == "Nginx") {
                    c = f
                } else {
                    if (l[h].name == "Apache") {
                        g = f
                    } else {
                        e += f
                    }
                }
            }
            c += e;
            g += e;

            g = g.replace(new RegExp(/(data_)/g), "apache_").replace(new RegExp(/(select_)/g), "apache_select_");
            var k = layer.open({
                type: 1,
                title: lan.bt.install_title,
                area: ["670px", "610px"],
                closeBtn: 2,
                shadeClose: false,
                content: "<div class='rec-install'><div class='important-title'><p><span class='glyphicon glyphicon-alert' style='color: #f39c12; margin-right: 10px;'></span>" + lan.bt.install_ps + " <a href='javascript:jump()' style='color:#20a53a'>" + lan.bt.install_s + "</a> " + lan.bt.install_s1 + "</p></div><div class='rec-box'><h3>" + lan.bt.install_lnmp + "</h3><div class='rec-box-con'><ul class='rec-list'>" + c + "</ul><p class='fangshi1'>" + lan.bt.install_type + "：<label data-title='" + lan.bt.install_rpm_title + "'><span>" + lan.bt.install_rpm + "</span><input type='checkbox' checked></label><label data-title='" + lan.bt.install_src_title + "'><span>" + lan.bt.install_src + "</span><input type='checkbox'></label></p><div class='onekey'>" + lan.bt.install_key + "</div></div></div><div class='rec-box' style='margin-left:16px'><h3>LAMP</h3><div class='rec-box-con'><ul class='rec-list'>" + g + "</ul><p class='fangshi1'>" + lan.bt.install_type + "：<label data-title='" + lan.bt.install_rpm_title + "'><span>" + lan.bt.install_rpm + "</span><input type='checkbox' checked></label><label data-title='" + lan.bt.install_src_title + "'><span>" + lan.bt.install_src + "</span><input type='checkbox'></label></p><div class='onekey'>"+lan.bt.install_key +"</div></div></div></div>",
                success:function(){
                	form_group.select_all([
                		'#select_Nginx',
                		'#select_MySQL',
                		'#select_Pure-Ftpd',
                		'#select_PHP',
                		'#select_phpMyAdmin',
                		'#select_DNS-Server',
                		'#select_Mail-Server',
                		'#apache_select_Apache',
                		'#apache_select_MySQL',
                		'#apache_select_Pure-Ftpd',
                		'#apache_select_PHP',
                		'#apache_select_phpMyAdmin',
                		'#apache_select_DNS-Server',
                		'#apache_select_Mail-Server',
                	]);
                	form_group.checkbox();
                	$('.layui-layer-content').css('overflow','inherit');
                	$('.fangshi1 label').click(function(){
                	    var input = $(this).find('input'),siblings_label = input.parents('label').siblings()
                	    input.prop('checked','checked').next().addClass('active');
                	    siblings_label.find('input').removeAttr('checked').next().removeClass('active');
                	});
		            var loadT = '';
					$('.fangshi1 label').hover(function(){
						var _title = $(this).attr('data-title'),_that = $(this);
						loadT = setTimeout(function(){
							layer.tips(_title,_that[0], {
							  tips: [1, '#20a53a'], //还可配置颜色
							  time:0
							});
						},500);
					},function(){
						clearTimeout(loadT);
						layer.closeAll('tips');
					});
                }
			});
            $(".sl-s-info").change(function() {
				var p = $(this).find("option:selected").text();
				var n = $(this).attr("id");
				p = p.toLowerCase();
				$(this).parents("li").find("input").attr("data-info", p)
			});
			$("#apache_select_PHP").change(function() {
				var n = $(this).val();
				j(n, "apache_select_", "apache_")
			});
			$("#select_PHP").change(function() {
				var n = $(this).val();
				j(n, "select_", "data_")
			});

			function j(p, r, q) {
				var n = "4.4";
				switch(p) {
					case "5.2":
						n = "4.0";
						break;
					case "5.3":
						n = "4.0";
						break;
					case "5.4":
						n = "4.4";
						break;
					case "5.5":
						n = "4.4";
						break;
					default:
						n = "4.9"
				}
				$("#" + r + "phpMyAdmin option[value='" + n + "']").attr("selected", "selected").siblings().removeAttr("selected");
				$("#"+q+"phpMyAdmin").attr("data-info", "phpmyadmin " + n)
			}
			$("#select_MySQL,#apache_select_MySQL").change(function() {
				var n = $(this).val();
				a(n)
			});

			$("#apache_select_Apache").change(function(){
				var apacheVersion = $(this).val();
				if(apacheVersion == '2.2'){
					layer.msg(lan.bt.install_apache22);
				}else{
					layer.msg(lan.bt.install_apache24);
				}
			});

			$("#apache_select_PHP").change(function(){
				var apacheVersion = $("#apache_select_Apache").val();
				var phpVersion = $(this).val();
				if(apacheVersion == '2.2'){
					if(phpVersion != '5.2' && phpVersion != '5.3' && phpVersion != '5.4'){
						layer.msg(lan.bt.insatll_s22+'PHP-' + phpVersion,{icon:5});
						$(this).val("5.4");
						$("#apache_PHP").attr('data-info','php 5.4');
						return false;
					}
				}else{
					if(phpVersion == '5.2'){
						layer.msg(lan.bt.insatll_s24+'PHP-' + phpVersion,{icon:5});
						$(this).val("5.4");
						$("#apache_PHP").attr('data-info','php 5.4');
						return false;
					}
				}
			});

			function a(n) {
				memSize = bt.get_cookie("memSize");
				max = 64;
				msg = "64M";
				switch(n) {
					case "5.1":
						max = 256;
						msg = "256M";
						break;
					case "5.7":
						max = 1500;
						msg = "2GB";
                        break;
                    case "8.0":
                        max = 5000;
                        msg = "6GB";
                        break;
					case "5.6":
						max = 800;
						msg = "1GB";
						break;
					case "AliSQL":
						max = 800;
						msg = "1GB";
						break;
					case "mariadb_10.0":
						max = 800;
						msg = "1GB";
						break;
					case "mariadb_10.1":
						max = 1500;
						msg = "2GB";
						break
				}
				if(memSize < max) {
					layer.msg( lan.bt.insatll_mem.replace("{1}",msg).replace("{2}",n), {
						icon: 5
					})
				}
			}
			var de = null;
			$(".onekey").click(function() {
				if(de) return;
				var v = $(this).prev().find("input").eq(0).prop("checked") ? "1" : "0";
				var r = $(this).parents(".rec-box-con").find(".rec-list li").length;
				var n = "";
				var q = "";
				var p = "";
				var x = "";
				var s = "";
				de = true;
				for(var t = 0; t < r; t++) {
					var w = $(this).parents(".rec-box-con").find("ul li").eq(t);
					var u = w.find("input");
					if(u.prop("checked")) {
						n += u.attr("data-info") + ","
					}
				}
				q = n.split(",");
				loadT = layer.msg(lan.bt.install_to, {
					icon: 16,
					time: 0,
					shade: [0.3, "#000"]
				});

				install_plugin(q);

				function install_plugin(q){
					if(!q[0]) return;
					p = q[0].split(" ")[0].toLowerCase();
					x = q[0].split(" ")[1];
					if(p=='pure-ftpd') p = 'pureftpd';
					if(p=='php') p = 'php-'+x;
					if(p=='model-server') p = 'dns_manager';
					if(p=='mail-server') p = 'mail_sys';

                    s = "sName=" + p + "&version=" + x + "&type=" + v + "&id=" + (t + 1);
					bt.send('install_plugin','plugin/install_plugin',s,function(){
						q.splice(0,1);
						install_plugin(q);
					});
				}

				layer.close(loadT);
				layer.close(k);
				setTimeout(function() {
					GetTaskCount()
				}, 2000);
				layer.msg(lan.bt.install_ok, {
					icon: 1
				});
				setTimeout(function() {
					task();
				}, 1000);
      });
    });
  }
}

bt.weixin = {
    settiming: '',
    relHeight: 500,
    relWidth: 500,
    userLength: '',
    get_user_info: function(callback) {
        bt.send('get_user_info', 'panel_wxapp/get_user_info', {}, function(rdata) {
            if (callback) callback(rdata);
        }, 1)
    },
    init: function() {
        var _this = this;
        $('.layui-layer-page').css('display', 'none');
        $('.layui-layer-page').width(_this.relWidth);
        $('.layui-layer-page').height(_this.relHeight);
        $('.bt-w-menu').height((_this.relWidth - 1) - $('.layui-layer-title').height());
        var width = $(document).width();
        var height = $(document).height();
        var boxwidth = (width / 2) - (_this.relWidth / 2);
        var boxheight = (height / 2) - (_this.relHeight / 2);
        $('.layui-layer-page').css({
            'left': boxwidth + 'px',
            'top': boxheight + 'px'
        });
        $('.boxConter,.layui-layer-page').css('display', 'block');
        $('.layui-layer-close').click(function(event) {
            window.clearInterval(_this.settiming);
        });
        this.get_user_details();
        $('.iconCode').hide();
        $('.personalDetails').show();
    },
    // 获取二维码
    get_qrcode: function() {
        var _this = this;
        var qrLoading = bt.load(lan.config.config_qrcode);

        bt.send('blind_qrcode', 'panel_wxapp/blind_qrcode', {}, function(res) {
            qrLoading.close();
            if (res.status) {
                $('#QRcode').empty();
                $('#QRcode').qrcode({
                    render: "canvas", //也可以替换为table
                    width: 200,
                    height: 200,
                    text: res.msg
                });
                _this.settiming = setInterval(function() {
                    _this.verify_binding();
                }, 2000);
            } else {
                bt.msg(res);
            }
        })
    },
    // 获取用户信息
    get_user_details: function(type) {
        var _this = this;
        var conter = '';
        _this.get_user_info(function(res) {
            clearInterval(_this.settiming);
            if (!res.status) {
                res.time = 3000;
                bt.msg(res);

                $('.iconCode').hide();
                return false;
            }
            if (JSON.stringify(res.msg) == '{}') {
                if (type) {
                    bt.msg({ msg: lan.config.qrcode_no_list, icon: 2 })
                } else {
                    _this.get_qrcode();
                }
                $('.iconCode').show();
                $('.personalDetails').hide();
                return false;
            }
            $('.iconCode').hide();
            $('.personalDetails').show();
            var datas = res.msg;
            for (var item in datas) {
                conter += '<li class="item">\
								<div class="head_img"><img src="' + datas[item].avatarUrl + '" title="' + lan.public_backup.user_img + '" /></div>\
								<div class="nick_name"><span>' + lan.public_backup.nick_name + '</span><span class="nick"></span>' + datas[item].nickName + '</div>\
								<div class="cancelBind">\
									<a href="javascript:;" class="btlink" title="' + lan.public_backup.cancel_wechat_bind + '" onclick="bt.weixin.cancel_bind(' + item + ')">' + lan.public_backup.cancel_bind + '</a>\
								</div>\
							</li>'
            }
            conter += '<li class="item addweChat" style="height:45px;"><a href="javascript:;" class="btlink" onclick="bt.weixin.add_wx_view()"><span class="glyphicon glyphicon-plus"></span>' + lan.public_backup.add_account_bind + '</a></li>'
            $('.userList').empty().append(conter);
        })
    },
    // 添加绑定视图
    add_wx_view: function() {
        $('.iconCode').show();
        $('.personalDetails').hide();
        this.get_qrcode();
    },
    // 取消当前绑定
    cancel_bind: function(uid) {
        var _this = this;
        var bdinding = layer.confirm(lan.public_backup.unbind_account, {
            btn: [lan.public_backup.confirm, lan.public_backup.cancel],
            icon: 3,
            title: lan.public_backup.unbind
        }, function() {
            bt.send("blind_del", "panel_wxapp/blind_del", { uid: uid }, function(res) {
                bt.msg(res);
                _this.get_user_details();
            })
        }, function() {
            layer.close(bdinding);
        });
    },
    // 监听是否绑定
    verify_binding: function() {
        var _this = this;
        bt.send('blind_result', 'panel_wxapp/blind_result', {}, function(res) {
            if (res) {
                bt.msg({ status: true, msg: lan.public_backup.bind_success });
                clearInterval(_this.settiming);
                _this.get_user_details();
            }
        })
    },
    open_wxapp: function() {
        var rhtml = '<div class="boxConter" style="display: none">\
								<div class="iconCode" >\
									<div class="box-conter">\
										<div id="QRcode"></div>\
										<div class="codeTip">\
											<ul>\
												<li>1、' + lan.public_backup.open_bt_small_app + '<span class="btlink weChat">' + lan.public_backup.app_qr_core + '<div class="weChatSamll"><img src="https://app.bt.cn/static/app.png"></div></span></li>\
												<li>2、' + lan.public_backup.scan_qr_core + '</li>\
											</ul>\
											<span><a href="javascript:;" title="' + lan.public_backup.return_bind_list + '" class="btlink" style="margin: 0 auto" onclick="bt.weixin.get_user_details(true)">' + lan.public_backup.read_bind_list + '</a></span>\
										</div>\
									</div>\
								</div>\
								<div class="personalDetails" style="display: none">\
									<ul class="userList"></ul>\
								</div>\
							</div>'

        bt.open({
            type: 1,
            title: lan.public_backup.bind_wechat,
            area: '500px',
            shadeClose: false,
            content: rhtml
        })
        bt.weixin.init();
    }
};



bt.ftp = {
    get_list: function(page, search, callback) {
        if (page == undefined) page = 1
        search = search == undefined ? '' : search;
        var order = bt.get_cookie('order') ? '&order=' + bt.get_cookie('order') : '';

        var data = 'tojs=ftp.get_list&table=ftps&limit=15&p=' + page + '&search=' + search + order;
        bt.pub.get_data(data, function(rdata) {
            if (callback) callback(rdata);
        })
    },
    add: function(callback) {
        bt.data.ftp.add.list[1].items[0].value = bt.get_random(16);
        var bs = bt.render_form(bt.data.ftp.add, function(rdata) {
            if (callback) callback(rdata);
        });
        $('.path' + bs).val($("#defaultPath").text());
    },
    set_password: function(callback) {
        var bs = bt.render_form(bt.data.ftp.set_password, function(rdata) {
            if (callback) callback(rdata);
        });
        return bs;
    },
    del: function(id, username, callback) {
        var loading = bt.load(lan.get('del_all_task_the', [username]));
        bt.send('DeleteUser', 'ftp/DeleteUser', { id: id, username: username }, function(rdata) {
            loading.close();
            if (callback) callback(rdata);
        })
    },
    set_status: function(id, username, status, callback) {
        var loadT = bt.load(lan.public.the);
        var data = 'id=' + id + '&username=' + username + '&status=' + status;
        bt.send('SetStatus', 'ftp/SetStatus', data, function(rdata) {
            loadT.close();
            if (callback) callback(rdata);
            bt.msg(rdata);
        })
    },
    set_port: function(callback) {
        var bs = bt.render_form(bt.data.ftp.set_port, function(rdata) {
            if (callback) callback(rdata);
        });
        return bs;
    }
}

bt.recycle_bin = {
    open_recycle_bin: function(type) {
        if (type == undefined) type = 1;
        bt.files.get_recycle_bin(type, function(rdata) {
            var data = [];
            switch (type) {
                case 2:
                    data = rdata.dirs;
                    break;
                case 3:
                    data = rdata.files;
                    break;
                case 4:
                case 5:
                case 6:
                    for (var i = 0; i < rdata.files.length; i++) {
                        if (type == 6 && bt.contains(rdata.files[i].name, 'BTDB_')) {
                            data.push(rdata.files[i]);
                        } else {
                            if (type == 4 && bt.check_img(rdata.files[i].name)) {
                                data.push(rdata.files[i]);
                            } else if (type == 5 && !bt.check_img(rdata.files[i].name)) {
                                data.push(rdata.files[i]);
                            }
                        }
                    }
                    break;
                default:
                    data = rdata.dirs.concat(rdata.files);
                    break;
            }
            if ($('#tab_recycle_bin').length <= 0) {
                bt.open({
                    type: 1,
                    skin: 'demo-class',
                    area: ['80%', '672px'],
                    title: lan.files.recycle_bin_title,
                    closeBtn: 2,
                    shift: 5,
                    shadeClose: false,
                    content: '<div class="re-head">\
							<div style="margin-left: 3px;" class="ss-text">\
			                        <em>' + lan.files.recycle_bin_on + '</em>\
			                        <div class="ssh-item">\
			                                <input class="btswitch btswitch-ios" id="Set_Recycle_bin" type="checkbox" ' + (rdata.status ? 'checked' : '') + '>\
			                                <label class="btswitch-btn" for="Set_Recycle_bin" onclick="bt.files.set_recycle_bin()"></label>\
			                        </div>\
			                        <em style="margin-left: 20px;">' + lan.files.recycle_bin_on_db + '</em>\
			                        <div class="ssh-item">\
			                                <input class="btswitch btswitch-ios" id="Set_Recycle_bin_db" type="checkbox" ' + (rdata.status_db ? 'checked' : '') + '>\
			                                <label class="btswitch-btn" for="Set_Recycle_bin_db" onclick="bt.files.set_recycle_bin(1)"></label>\
			                        </div>\
			                </div>\
							<span style="line-height: 32px; margin-left: 30px;">' + lan.files.recycle_bin_ps + '</span>\
			                <button style="float: right" class="btn btn-default btn-sm" onclick="bt.recycle_bin.clear_recycle_bin();">' + lan.files.recycle_bin_close + '</button>\
							</div>\
							<div class="re-con">\
								<div class="re-con-menu"></div>\
								<div class="re-con-con">\
								<div class="divtable">\
									<table id="tab_recycle_bin" width="100%" class="table table-hover"></table>\
								</div></div></div>'
                });
            }

            setTimeout(function() {
                var menus = [
                    { title: lan.files.recycle_bin_type1, click: 'bt.recycle_bin.open_recycle_bin(1)' },
                    { title: lan.files.recycle_bin_type2, click: 'bt.recycle_bin.open_recycle_bin(2)' },
                    { title: lan.files.recycle_bin_type3, click: 'bt.recycle_bin.open_recycle_bin(3)' },
                    { title: lan.files.recycle_bin_type4, click: 'bt.recycle_bin.open_recycle_bin(4)' },
                    { title: lan.files.recycle_bin_type5, click: 'bt.recycle_bin.open_recycle_bin(5)' },
                    { title: lan.files.recycle_bin_type6, click: 'bt.recycle_bin.open_recycle_bin(6)' }
                ];
                var m_html = '';
                for (var i = 0; i < menus.length; i++) {
                    var c = type == (i + 1) ? 'class="on"' : '';
                    m_html += '<p ' + c + ' onclick="' + menus[i].click + '" >' + menus[i].title + '</p>';
                }
                $('.re-con-menu').html(m_html);
                var _tab = bt.render({
                    table: '#tab_recycle_bin',
                    columns: [
                        { field: 'name', title: lan.files.recycle_bin_th1 },
                        { field: 'dname', title: lan.files.recycle_bin_th2 },
                        {
                            field: 'size',
                            title: lan.files.recycle_bin_th3,
                            templet: function(item) {
                                return bt.format_size(item.size)
                            }
                        },
                        {
                            field: 'time',
                            title: lan.files.recycle_bin_th4,
                            templet: function(item) {
                                return bt.format_data(item.time);
                            }
                        },
                        {
                            field: 'opt',
                            title: lan.files.recycle_bin_th5,
                            align: 'right',
                            templet: function(item) {
                                var opt = '<a class="btlink" href="javascript:;" onclick="bt.recycle_bin.re_recycle_bin(\'' + item.rname + '\',' + type + ')">' + lan.public_backup.recover + '</a> | ';
                                opt += '<a class="btlink" href="javascript:;" onclick="bt.recycle_bin.del_recycle_bin(\'' + item.rname + '\',' + type + ')">' + lan.public_backup.permanent_delete + '</a>';
                                return opt;
                            }
                        },
                    ],
                    data: data
                });
            }, 100)
        })
    },
    clear_recycle_bin: function() {
        var _this = this;
        bt.files.clear_recycle_bin(function(rdata) {
            _this.open_recycle_bin(1);
            bt.msg(rdata);
        })
    },
    del_recycle_bin: function(path, type) {
        var _this = this;
        bt.files.del_recycle_bin(path, function(rdata) {
            if (rdata.status) _this.open_recycle_bin(type);
            bt.msg(rdata);
        })
    },
    re_recycle_bin: function(path, type) {
        var _this = this;
        bt.files.re_recycle_bin(path, function(rdata) {
            if (rdata.status) _this.open_recycle_bin(type);
            bt.msg(rdata);
        })
    }
}



bt.files = {
        get_path: function() {
            path = path = bt.get_cookie('Path');
            if (!path) {
                bt.msg({ msg: lan.get('lack_param', ['response']) });
                return;
            }
        },
        get_files: function(Path, searchV, callback) {
            var searchtype = Path;
            if (isNaN(Path)) {
                var p = '1';
            } else {
                var p = Path;
                Path = bt.get_cookie('Path');
            }
            var search = '';
            if (searchV.length > 1 && searchtype == "1") {
                search = "&search=" + searchV;
            }
            var showRow = bt.get_cookie('showRow');
            if (!showRow) showRow = '500';
            var totalSize = 0;
            var loadT = bt.load(lan.public.the);
            bt.send('get_files', 'files/GetDir', 'tojs=GetFiles&p=' + p + '&showRow=' + showRow + search + '&path=' + Path, function(rdata) {
                loadT.close();
                //bt.set_cookie('Path',rdata.PATH);
                if (callback) callback(rdata);
            })
        },
        get_recycle_bin: function(type, callback) {
            loading = bt.load(lan.public.the);
            bt.send('Get_Recycle_bin', 'files/Get_Recycle_bin', {}, function(rdata) {
                loading.close();
                if (callback) callback(rdata);
            })
        },
        re_recycle_bin: function(path, callback) {
            bt.confirm({ msg: lan.files.recycle_bin_re_msg, title: lan.files.recycle_bin_re_title }, function() {
                var loadT = bt.load(lan.files.recycle_bin_re_the);
                bt.send('Re_Recycle_bin', 'files/Re_Recycle_bin', 'path=' + path, function(rdata) {
                    loadT.close();
                    bt.msg(rdata);
                    if (callback) callback(rdata);
                })
            });
        },
        del_recycle_bin: function(path, callback) {
            bt.confirm({ msg: lan.files.recycle_bin_del_msg, title: lan.files.recycle_bin_del_title }, function() {
                var loadT = bt.load(lan.files.recycle_bin_del_the);
                bt.send('Re_Recycle_bin', 'files/Del_Recycle_bin', 'path=' + path, function(rdata) {
                    loadT.close();
                    bt.msg(rdata);
                    if (callback) callback(rdata);
                })
            });
        },
        clear_recycle_bin: function(callback) {
            bt.confirm({ msg: lan.files.recycle_bin_close_msg, title: lan.files.recycle_bin_close }, function() {
                var loadT = bt.load("<div class='myspeed'>" + lan.files.recycle_bin_close_the + "</div>");
                bt.send('Re_Recycle_bin', 'files/Close_Recycle_bin', {}, function(rdata) {
                    loadT.close();
                    bt.msg(rdata);
                    if (callback) callback(rdata);
                })
            });
        },
        set_recycle_bin: function(db) {
            var loadT = bt.load(lan.public.the);
            var data = {};
            if (db) data = { db: db }
            bt.send('Recycle_bin', 'files/Recycle_bin', data, function(rdata) {
                loadT.close();
                bt.msg(rdata);
            })
        },
        rename: function(fileName, type, callback) {
            if (type == undefined) type = 0;
            _this = this;
            path = _this.get_path();
            if (type) {
                var newFileName = path + '/' + $("#newFileName").val();
                var oldFileName = path + '/' + fileName;
                var loading = bt.load(lan.public.the);
                bt.send('MvFile', 'files/MvFile', 'sfile=' + oldFileName + '&dfile=' + newFileName, function(rdata) {
                    loading.close();
                    bt.msg(rdata);
                    if (callback) callback(rdata);
                });
                return;
            }
            bt.open({
                type: 1,
                shift: 5,
                closeBtn: 2,
                area: '320px',
                title: lan.files.file_menu_rename,
                content: '<div class="bt-form pd20 pb70">\
						<div class="line">\
						<input type="text" class="bt-input-text" name="Name" id="newFileName" value="' + fileName + '" placeholder="' + lan.files.file_name + '" style="width:100%" />\
						</div>\
						<div class="bt-form-submit-btn">\
						<button type="button" class="btn btn-danger btn-sm btn-title" onclick="layer.closeAll()">' + lan.public.close + '</button>\
						<button type="button" id="ReNameBtn" class="btn btn-success btn-sm btn-title">' + lan.public.save + '</button>\
						</div>\
					</div>'
            });
            setTimeout(function() {
                $("#ReNameBtn").click(function() {
                    _this.rename(fileName, 1, callback);
                })
                $("#newFileName").focus().keyup(function(e) {
                    if (e.keyCode == 13) $("#ReNameBtn").click();
                });
            }, 100)

        },
        get_file_body: function(path, callback) {
            bt.send('GetFileBody', 'files/GetFileBody', 'path=' + path, function(rdata) {
                if (callback) callback(rdata);
            })
        },
        set_file_body: function(path, data, encoding, callback) {
            var loading = bt.load(lan.site.saving_txt);
            bt.send('SaveFileBody', 'files/SaveFileBody', { path: path, data: data, encoding: encoding }, function(rdata) {
                loading.close();
                if (callback) callback(rdata);
            })
        },
        del_file: function(path, callback) {
            bt.confirm({ msg: lan.get('recycle_bin_confirm', [fileName]), title: lan.files.del_file }, function() {
                loading = bt.load(lan.public.the);
                bt.send('del_file', 'files/DeleteFile', 'path=' + path, function(rdata) {
                    loading.close();
                    bt.msg(rdata);
                    if (callback) callback(rdata);
                })
            })
        },
        del_dir: function(path, callback) {
            bt.confirm({ msg: lan.get('recycle_bin_confirm_dir', [fileName]), title: lan.files.del_file }, function() {
                loading = bt.load(lan.public.the);
                bt.send('DeleteDir', 'files/DeleteDir', 'path=' + path, function(rdata) {
                    loading.close();
                    bt.msg(rdata);
                    if (callback) callback(rdata);
                })
            })
        },
        cut_file: function(fileName, callback) //裁剪
            {
                bt.set_cookie('cutFileName', fileName);
                bt.set_cookie('copyFileName', null);
                bt.msg({ msg: lan.files.mv_ok, icon: 1, time: 1 })
                if (callback) callback(rdata);
            },
        copy_file: function(fileName, callback) {
            bt.set_cookie('cutFileName', null);
            bt.set_cookie('copyFileName', fileName);
            bt.msg({ msg: lan.files.copy_ok, icon: 1, time: 1 })
            if (callback) callback(rdata);
        },
        paste_file: function(fileName, callback) //粘贴
            {
                _this = this;
                path = _this.get_path();
                var copyName = bt.get_cookie('copyFileName');
                var cutName = bt.get_cookie('cutFileName');
                var filename = copyName;
                if (cutName != 'null' && cutName != undefined) filename = cutName;
                filename = filename.split('/').pop();

                bt.send('CheckExistsFiles', 'files/CheckExistsFiles', { dfile: path, filename: filename }, function(rdata) {
                    if (rdata.length > 0) {
                        var tbody = '';
                        for (var i = 0; i < rdata.length; i++) {
                            tbody += '<tr><td>' + rdata[i].filename + '</td><td>' + bt.format_size(rdata[i].size) + '</td><td>' + bt.format_data(rdata[i].mtime) + '</td></tr>';
                        }
                        var mbody = '<div class="divtable"><table class="table table-hover" width="100%" border="0" cellpadding="0" cellspacing="0"><thead><th>' + lan.bt.filename + '</th><th>' + lan.bt.file_size + '</th><th>' + lan.bt.etime + '</th></thead>\
							<tbody>' + tbody + '</tbody>\
							</table></div>';
                        bt.show_confirm(bt.files.file_conver_msg, mbody, function() {
                            _this.paste_to(path, copyName, cutName, fileName, callback);
                        })
                    } else {
                        _this.paste_to(path, copyName, cutName, fileName, callback);
                    }
                })
            },
        paste_to: function(path, copyName, cutName, fileName, callback) {
            if (copyName != 'null' && copyName != undefined) {
                var loading = bt.msg({ msg: lan.files.copy_the, icon: 16 });
                bt.send('CopyFile', 'files/CopyFile', 'sfile=' + copyName + '&dfile=' + path + '/' + fileName, function(rdata) {
                    loading.close();
                    bt.msg(rdata);
                    if (callback) callback(rdata);
                })
                bt.set_cookie('copyFileName', null);
                bt.set_cookie('cutFileName', null);
                return;
            }

            if (cutName != 'null' && cutName != undefined) {
                var loading = bt.msg({ msg: lan.files.copy_the, icon: 16 });
                bt.send('MvFile', 'files/MvFile', 'sfile=' + copyName + '&dfile=' + path + '/' + fileName, function(rdata) {
                    loading.close();
                    bt.msg(rdata);
                    if (callback) callback(rdata);
                });
                bt.set_cookie('copyFileName', null);
                bt.set_cookie('cutFileName', null);
                return;
            }
        },
        zip: function(dirName, submits, callback) {
            _this = this;
            if (submits != undefined) {
                if (dirName.indexOf(',') == -1) {
                    tmp = $("#sfile").val().split('/');
                    sfile = tmp[tmp.length - 1];
                } else {
                    sfile = dirName;
                }
                dfile = $("#dfile").val();
                layer.closeAll();
                var loading = bt.load(lan.files.zip_the);
                bt.send('Zip', 'files/Zip', 'sfile=' + sfile + '&dfile=' + dfile + '&type=tar&path=' + path, function(rdata) {
                    loading.close();
                    if (rdata == null || rdata == undefined) {
                        bt.msg({ msg: lan.files.zip_ok, icon: 1 })
                        if (callback) callback(rdata);
                        return;
                    }
                    bt.msg(rdata);
                    if (rdata.status)
                        if (callback) callback(rdata);;
                });
                return;
            }
            var ext = '.zip';
            if (bt.os == 'Linux') ext = '.tar.gz';

            param = dirName;
            if (dirName.indexOf(',') != -1) {
                tmp = path.split('/')
                dirName = path + '/' + tmp[tmp.length - 1]
            }
            bt.open({
                type: 1,
                shift: 5,
                closeBtn: 2,
                area: '650px',
                title: lan.files.zip_title,
                content: '<div class="bt-form pd20 pb70">' +
                    '<div class="line noborder">' +
                    '<input type="text" class="form-control" id="sfile" value="' + param + '" placeholder="" style="display:none" />' +
                    '<span>' + lan.files.zip_to + '</span><input type="text" class="bt-input-text" id="dfile" value="' + dirName + ext + '" placeholder="' + lan.files.zip_to + '" style="width: 75%; display: inline-block; margin: 0px 10px 0px 20px;" /><span class="glyphicon glyphicon-folder-open cursor" onclick="ChangePath(\'dfile\')"></span>' +
                    '</div>' +
                    '<div class="bt-form-submit-btn">' +
                    '<button type="button" class="btn btn-danger btn-sm btn-title" onclick="layer.closeAll()">' + lan.public.close + '</button>' +
                    '<button type="button" id="ReNameBtn" class="btn btn-success btn-sm btn-title"' + lan.files.file_menu_zip + '</button>' +
                    '</div>' +
                    '</div>'
            });

            setTimeout(function() {
                $("#dfile").change(function() {
                    var dfile = bt.rtrim($(this).val(), '/');
                    if (bt.check_zip(dfile) === -1) {
                        dfile += ext;
                        $(this).val(dfile)
                    }
                });
                $("#ReNameBtn").click(function() {
                    _this.zip(param, 1, callback);
                })
            }, 100);
        },
        un_zip: function(fileName, type, callback) // type: zip|tar
            {
                _this = this;
                if (type.length == 3) {
                    var sfile = encodeURIComponent($("#sfile").val());
                    var dfile = encodeURIComponent($("#dfile").val());
                    var password = encodeURIComponent($("#unpass").val());
                    coding = $("select[name='coding']").val();
                    layer.closeAll();
                    var loading = bt.load(lan.files.unzip_the);
                    bt.send('UnZip', 'files/UnZip', 'sfile=' + sfile + '&dfile=' + dfile + '&type=' + type + '&coding=' + coding + '&password=' + password, function(rdata) {
                        loading.close();
                        bt.msg(rdata);
                        if (callback) callback(rdata);
                    });
                    return
                }
                var path = bt.get_file_path(fileName);
                type = (type == 1) ? 'tar' : 'zip'
                var umpass = '';
                if (type == 'zip') {
                    umpass = '<div class="line"><span class="tname">' + lan.files.zip_pass_title + '</span><input type="text" class="bt-input-text" id="unpass" value="" placeholder="' + lan.files.zip_pass_msg + '" style="width:330px" /></div>'
                }
                bt.open({
                    type: 1,
                    shift: 5,
                    closeBtn: 2,
                    area: '490px',
                    title: lan.files.unzip_title,
                    content: '<div class="bt-form pd20 pb70">' +
                        '<div class="line unzipdiv">' +
                        '<span class="tname">' + lan.files.unzip_name + '</span><input type="text" class="bt-input-text" id="sfile" value="' + fileName + '" placeholder="' + lan.files.unzip_name_title + '" style="width:330px" /></div>' +
                        '<div class="line"><span class="tname">' + lan.files.unzip_to + '</span><input type="text" class="bt-input-text" id="dfile" value="' + path + '" placeholder="' + lan.files.unzip_to + '" style="width:330px" /></div>' + umpass +
                        '<div class="line"><span class="tname">' + lan.files.unzip_coding + '</span><select class="bt-input-text" name="coding">' +
                        '<option value="UTF-8">UTF-8</option>' +
                        '<option value="gb18030">GBK</option>' +
                        '</select>' +
                        '</div>' +
                        '<div class="bt-form-submit-btn">' +
                        '<button type="button" class="btn btn-danger btn-sm btn-title" onclick="layer.closeAll()">' + lan.public.close + '</button>' +
                        '<button type="button" id="ReNameBtn" class="btn btn-success btn-sm btn-title" >' + lan.files.file_menu_unzip + '</button>' +
                        '</div>' +
                        '</div>'
                });
                setTimeout(function() {

                    $("#ReNameBtn").click(function() {
                        _this.un_zip(fileName, type, callback);
                    })
                }, 100);
            },
        show_img: function(fileName) {
            var imgUrl = '/download?filename=' + fileName;
            bt.open({
                type: 1,
                closeBtn: 2,
                title: false,
                area: '500px',
                shadeClose: true,
                content: '<div class="showpicdiv"><img width="100%" src="' + imgUrl + '"></div>'
            });
            $(".layui-layer").css("top", "30%");
        },
        get_files_bytes: function(fileName, fileSize) {
            window.open('/download?filename=' + encodeURIComponent(fileName));
        },
        upload_files: function() {
            path = this.get_path();
            bt.open({
                type: 1,
                closeBtn: 2,
                title: lan.files.up_title,
                area: ['500px', '500px'],
                shadeClose: false,
                content: '<div class="fileUploadDiv"><input type="hidden" id="input-val" value="' + path + '" />\
					<input type="file" id="file_input"  multiple="true" autocomplete="off" />\
					<button type="button"  id="opt" autocomplete="off">' + lan.files.up_add + '</button>\
					<button type="button" id="up" autocomplete="off" >' + lan.files.up_start + '</button>\
					<span id="totalProgress" style="position: absolute;top: 7px;right: 147px;"></span>\
					<span style="float:right;margin-top: 9px;">\
					<font>' + lan.files.up_coding + ':</font>\
					<select id="fileCodeing" >\
						<option value="byte">' + lan.files.up_bin + '</option>\
						<option value="utf-8">UTF-8</option>\
						<option value="gb18030">GB2312</option>\
					</select>\
					</span>\
					<button type="button" id="filesClose" autocomplete="off" onClick="layer.closeAll()" >' + lan.public.close + '</button>\
					<ul id="up_box"></ul></div>'
            });
            UploadStart();
        },
        set_chmod: function(action, fileName, callback) {
            _this = this;
            if (action == 1) {
                var chmod = $("#access").val();
                var chown = $("#chown").val();
                var data = 'filename=' + fileName + '&user=' + chown + '&access=' + chmod;
                var loadT = bt.load(lan.public.config);
                bt.send('SetFileAccess', 'files/SetFileAccess', data, function(rdata) {
                    loadT.close();
                    if (rdata.status) layer.closeAll();
                    bt.msg(rdata);
                    if (callback) callback(rdata);
                });
                return;
            }

            var toExec = fileName == lan.files.all ? 'Batch(3,1)' : '_this.set_chmod(1,\'' + fileName + '\',callback)';

            bt.send('GetFileAccess', 'files/GetFileAccess', 'filename=' + fileName, function(rdata) {
                if (bt.os == 'Linux') {
                    bt.open({
                        type: 1,
                        title: lan.files.set_auth + '[' + fileName + ']',
                        area: '400px',
                        shadeClose: false,
                        content: '<div class="setchmod bt-form ptb15 pb70">\
								<fieldset>\
									<legend>' + lan.files.file_own + '</legend>\
									<p><input type="checkbox" id="owner_r" />' + lan.files.file_read + '</p>\
									<p><input type="checkbox" id="owner_w" />' + lan.files.file_write + '</p>\
									<p><input type="checkbox" id="owner_x" />' + lan.files.file_exec + '</p>\
								</fieldset>\
								<fieldset>\
									<legend>' + lan.files.file_group + '</legend>\
									<p><input type="checkbox" id="group_r" />' + lan.files.file_read + '</p>\
									<p><input type="checkbox" id="group_w" />' + lan.files.file_write + '</p>\
									<p><input type="checkbox" id="group_x" />' + lan.files.file_exec + '</p>\
								</fieldset>\
								<fieldset>\
									<legend>' + lan.files.file_public + '</legend>\
									<p><input type="checkbox" id="public_r" />' + lan.files.file_read + '</p>\
									<p><input type="checkbox" id="public_w" />' + lan.files.file_write + '</p>\
									<p><input type="checkbox" id="public_x" />' + lan.files.file_exec + '</p>\
								</fieldset>\
								<div class="setchmodnum"><input class="bt-input-text" type="text" id="access" maxlength="3" value="' + rdata.chmod + '">' + lan.files.file_menu_auth + '，\
								<span>' + lan.files.file_own + '\
								<select id="chown" class="bt-input-text">\
									<option value="www" ' + (rdata.chown == 'www' ? 'selected="selected"' : '') + '>www</option>\
									<option value="mysql" ' + (rdata.chown == 'mysql' ? 'selected="selected"' : '') + '>mysql</option>\
									<option value="root" ' + (rdata.chown == 'root' ? 'selected="selected"' : '') + '>root</option>\
								</select></span></div>\
								<div class="bt-form-submit-btn">\
									<button type="button" class="btn btn-danger btn-sm btn-title" onclick="layer.closeAll()">' + lan.public.close + '</button>\
							        <button type="button" class="btn btn-success btn-sm btn-title" onclick="' + toExec + '" >' + lan.public.ok + '</button>\
						        </div>\
							</div>'
                    });

                    settimeout(function() {
                        _this.on_linux_access();
                        $("#access").keyup(function() {
                            _this.on_linux_access();
                        });

                        $("input[type=checkbox]").change(function() {
                            var idName = ['owner', 'group', 'public'];
                            var onacc = '';
                            for (var n = 0; n < idName.length; n++) {
                                var access = 0;
                                access += $("#" + idName[n] + "_x").prop('checked') ? 1 : 0;
                                access += $("#" + idName[n] + "_w").prop('checked') ? 2 : 0;
                                access += $("#" + idName[n] + "_r").prop('checked') ? 4 : 0;
                                onacc += access;
                            }
                            $("#access").val(onacc);
                        });
                    }, 100)
                }
            })
        },
        on_linux_access: function() {
            var access = $("#access").val();
            var idName = ['owner', 'group', 'public'];
            for (var n = 0; n < idName.length; n++) {
                $("#" + idName[n] + "_x").prop('checked', false);
                $("#" + idName[n] + "_w").prop('checked', false);
                $("#" + idName[n] + "_r").prop('checked', false);
            }
            for (var i = 0; i < access.length; i++) {
                var onacc = access.substr(i, 1);
                if (i > idName.length) continue;
                if (onacc > 7) $("#access").val(access.substr(0, access.length - 1));
                switch (onacc) {
                    case '1':
                        $("#" + idName[i] + "_x").prop('checked', true);
                        break;
                    case '2':
                        $("#" + idName[i] + "_w").prop('checked', true);
                        break;
                    case '3':
                        $("#" + idName[i] + "_x").prop('checked', true);
                        $("#" + idName[i] + "_w").prop('checked', true);
                        break;
                    case '4':
                        $("#" + idName[i] + "_r").prop('checked', true);
                        break;
                    case '5':
                        $("#" + idName[i] + "_r").prop('checked', true);
                        $("#" + idName[i] + "_x").prop('checked', true);
                        break;
                    case '6':
                        $("#" + idName[i] + "_r").prop('checked', true);
                        $("#" + idName[i] + "_w").prop('checked', true);
                        break;
                    case '7':
                        $("#" + idName[i] + "_r").prop('checked', true);
                        $("#" + idName[i] + "_w").prop('checked', true);
                        $("#" + idName[i] + "_x").prop('checked', true);
                        break;
                }
            }
        },
        on_win_access: function() {

        },
        get_right_click: function(type, path, name) {
            _this = this;
            var displayZip = bt.check_zip(type);
            var options = {
                items: [
                    { text: lan.files.file_menu_copy, onclick: function() { _this.copy_file(path) } },
                    { text: lan.files.file_menu_mv, onclick: function() { _this.cut_file(path) } },
                    { text: lan.files.file_menu_rename, onclick: function() { _this.rename(path, name) } },
                    { text: lan.files.file_menu_auth, onclick: function() { _this.set_chmod(0, path) } },
                    { text: lan.files.file_menu_zip, onclick: function() { _this.zip(path) } }

                ]
            };
            if (type == "dir") {
                options.items.push({ text: lan.files.file_menu_del, onclick: function() { _this.del_dir(path) } });
            } else if (isText(type)) {
                options.items.push({ text: lan.files.file_menu_edit, onclick: function() { bt.on_edit_file(0, path) } }, { text: lan.files.file_menu_down, onclick: function() { _this.get_files_bytes(path) } }, { text: lan.files.file_menu_del, onclick: function() { _this.del_file(path) } });
            } else if (displayZip != -1) {
                options.items.push({ text: lan.files.file_menu_unzip, onclick: function() { _this.un_zip(path, displayZip) } }, { text: lan.files.file_menu_down, onclick: function() { _this.get_files_bytes(path) } }, { text: lan.files.file_menu_del, onclick: function() { _this.del_file(path) } });
            } else if (isImage(type)) {
                options.items.push({ text: lan.files.file_menu_img, onclick: function() { _this.show_img(path) } }, { text: lan.files.file_menu_down, onclick: function() { _this.get_files_bytes(path) } }, { text: lan.files.file_menu_del, onclick: function() { _this.del_file(path) } });
            } else {
                options.items.push({ text: lan.files.file_menu_down, onclick: function() { _this.get_files_bytes(path) } }, { text: lan.files.file_menu_del, onclick: function() { _this.del_file(path) } });
            }
            return options;
        },
        get_dir_size: function(path, callback) {
            if (!path) path = this.get_path();
            // var loading = bt.load(lan.public.the);
            bt.send('GetDirSize', 'files/GetDirSize', { path: path }, function(rdata) {
                // loading.close();
                if (callback) callback(rdata);
            })
        },
        batch: function(type, access, callback) {
            _this = this;

            var el = document.getElementsByTagName('input');
            var len = el.length;
            var data = 'path=' + path + '&type=' + type;
            var name = 'data';

            var oldType = bt.get_cookie('BatchPaste');

            for (var i = 0; i < len; i++) {
                if (el[i].checked == true && el[i].value != 'on') {
                    data += '&' + name + '=' + el[i].value;
                }
            }

            if (type == 3 && access == undefined) {
                _this.set_chmod(0, lan.files.all);
                return;
            }

            if (type < 3) bt.set_cookie('BatchSelected', '1');
            bt.set_cookie('BatchPaste', type);

            if (access == 1) {
                var access = $("#access").val();
                var chown = $("#chown").val();
                data += '&access=' + access + '&user=' + chown;
                layer.closeAll();
            }
            if (type == 4) {
                AllDeleteFileSub(data, path);
                bt.set_cookie('BatchPaste', oldType);
                return;
            }

            if (type == 5) {
                var names = '';
                for (var i = 0; i < len; i++) {
                    if (el[i].checked == true && el[i].value != 'on') {
                        names += el[i].value + ',';
                    }
                }
                _this.zip(names);
                return;
            }

            myloadT = bt.load("<div class='myspeed'>" + lan.public.the + "</div>");
            setTimeout(function() { getSpeed('.myspeed'); }, 1000);
            bt.send('SetBatchData', 'files/SetBatchData', data, function(rdata) {
                myloadT.close();
                bt.msg(rdata);
                if (callback) callback(rdata);
            })
        },
        download_file: function(action, callback) {
            path = bt.get_cookie('Path');
            if (action == 1) {
                var fUrl = $("#mUrl").val();
                fUrl = fUrl;
                fpath = $("#dpath").val();
                fname = $("#dfilename").val();
                layer.closeAll();
                loading = bt.load(lan.files.down_task);
                bt.send('DownloadFile', 'files/DownloadFile', 'path=' + fpath + '&url=' + fUrl + '&filename=' + fname, function(rdata) {
                    loading.close();
                    bt.msg(rdata);
                    if (callback) callback(rdata);
                });
                return;
            }
            layer.open({
                type: 1,
                shift: 5,
                closeBtn: 2,
                area: '500px',
                title: lan.files.down_title,
                content: '<form class="bt-form pd20 pb70">\
						<div class="line">\
						<span class="tname">' + lan.files.down_url + ':</span><input type="text" class="bt-input-text" name="url" id="mUrl" value="" placeholder="' + lan.files.down_url + '" style="width:330px" />\
						</div>\
						<div class="line">\
						<span class="tname ">' + lan.files.down_to + ':</span><input type="text" class="bt-input-text" name="path" id="dpath" value="' + path + '" placeholder="' + lan.files.down_to + '" style="width:330px" />\
						</div>\
						<div class="line">\
						<span class="tname">' + lan.files.file_name + ':</span><input type="text" class="bt-input-text" name="filename" id="dfilename" value="" placeholder="' + lan.files.down_save + '" style="width:330px" />\
						</div>\
						<div class="bt-form-submit-btn">\
						<button type="button" class="btn btn-danger btn-sm" onclick="layer.closeAll()">' + lan.public.close + '</button>\
						<button type="button" id="dlok" class="btn btn-success btn-sm dlok" onclick="DownloadFile(1)">' + lan.public.ok + '</button>\
						</div>\
					</form>'
            });
            fly("dlok");
            $("#mUrl").keyup(function() {
                durl = $(this).val()
                tmp = durl.split('/')
                $("#dfilename").val(tmp[tmp.length - 1])
            });
        }
    }
    // 任务管理器
bt.crontab = {
    // 执行计划任务请求
    start_task_send: function(id, name) {
        var that = this,
            loading = bt.load();
        bt.send('start_task_send', 'crontab/StartTask', { id: id }, function(rdata) {
            loading.close();
            rdata.time = 2000;
            bt.msg(rdata);
        });
    },

    // 删除计划任务
    del_task_send: function(id, name) {
        bt.show_confirm(lan.public_backup.del + '[' + name + ']', lan.public_backup.del_task, function() {
            bt.send('del_task_send', 'crontab/DelCrontab', { id: id }, function(rdata) {
                loading.close();
                rdata.time = 2000;
                bt.msg(rdata);
                that.get_crontab_list();
            });
        });
    },

    // 设置计划任务状态
    set_crontab_status: function(id, status, callback) {
        var that = this,
            loading = bt.load();
        bt.confirm({ title: lan.public_backup.tips, msg: status ? lan.public_backup.stop_crontab : lan.public_backup.start_crontab }, function() {
            bt.send('set_crontab_status', 'crontab/set_cron_status', { id: id }, function(rdata) {
                loading.close();
                if (callback) callback(rdata)
            });
        });
    },

    // 编辑计划任务脚本
    edit_crontab_file: function(echo) {
        bt.pub.on_edit_file(0, '/www/server/cron/' + echo);
    },

    // 编辑计划任务
    edit_crontab: function(id, data) {
        var that = this,
            loading = bt.load(lan.public_backup.submit_data);
        bt.send('edit_crontab', 'crontab/modify_crond', data, function(rdata) {
            loading.close();
            if (rdata.status) {
                // that.get_crontab_list();
                layer.msg(rdata.msg, { icon: 1 });
            } else {
                layer.msg(rdata.msg, { icon: 2 });
            }
        });
    },

    // 获取计划任务日志
    get_logs_crontab: function(id, name) {
        var that = this;
        bt.send('get_logs_crontab', 'crontab/GetLogs', { id: id }, function(rdata) {
            if (!rdata.status) {
                rdata.time = 1000;
                bt.msg(rdata);
            } else {
                bt.open({
                    type: 1,
                    title: lan.public_backup.read_log + '-[' + name + ']',
                    area: ['700px', '520px'],
                    shadeClose: false,
                    closeBtn: 1,
                    content: '<div class="setchmod bt-form pd20 pb70">' +
                        '<pre class="crontab-log" style="overflow: auto; border: 0px none; line-height:28px;padding: 15px; margin: 0px; height: 405px; background-color: rgb(51,51,51);color:#f1f1f1;font-family: \"' + lan.public_backup.microsoft_yahei + '\"">' + (rdata.msg == '' ? lan.public_backup.log_empty : rdata.msg) + '</pre>' +
                        '<div class="bt-form-submit-btn" style="margin-top: 0px;">' +
                        '<button type="button" class="layui-btn layui-btn-sm" onclick="bt.crontab.del_logs_crontab(' + id + ')">' + lan.public.empty + '</button>' +
                        '<button type="button" class="layui-btn layui-btn-sm layui-btn-primary" onclick="layer.closeAll()">' + lan.public.close + '</button>' +
                        '</div>' +
                        '</div>'
                })
                setTimeout(function() {
                    var div = document.getElementsByClassName('crontab-log')[0]
                    div.scrollTop = div.scrollHeight;
                }, 200);
            }
        })
    },

    // 删除计划任务日志
    del_logs_crontab: function(id, name) {
        var that = this,
            loading = bt.load();
        bt.send('del_logs_crontab', 'crontab/DelLogs', { id: id }, function(rdata) {
            loading.close();
            layer.closeAll();
            rdata.time = 2000;
            bt.msg(rdata);
        });
    },

    // 获取计划任务列表
    get_crontab_list: function(status, callback) {
        var that = this;
        var loading = bt.load();
        bt.send('get_crontab_list', 'crontab/GetCrontab', {}, function(rdata) {
            loading.close();
            if (callback) callback(rdata);
        });
    },

    // 获取站点和备份位置信息
    get_data_list: function(type, name) {
        var that = this;
        bt.send('get_data_list', 'crontab/GetDataList', { type: type }, function(rdata) {
            that.backupsList.siteList = [{ 'name': 'ALL', 'ps': lan.public_backup.all }]
            that.backupsList.optList = [{ 'name': lan.public_backup.server_disk, 'value': 'localhost' }]
            that.backupsList.siteList = that.backupsList.siteList.concat(rdata.data);
            that.backupsList.optList = that.backupsList.optList.concat(rdata.orderOpt);
            that.initFrom["crontab-name"] = name + "[" + that.backupsList.siteList[that.initFrom['crontab-site']].name + "]";
            that.insert_control_from(that.initFrom['crontab-submit']);
        });
    },

    // 添加计划任务请求
    add_control_send: function(data) {
        var that = this,
            loading = bt.load(lan.public_backup.submit_data);
        bt.send('addCrontab', 'crontab/AddCrontab', data, function(rdata) {
            loading.close();
            if (rdata.status) {
                that.insert_control_from(true, true);
                that.get_crontab_list();
                layer.msg(rdata.msg, { icon: 1 });
            } else {
                layer.msg(rdata.msg, { icon: 2 });
            }
        });
    },
    get_crontab_find: function(id, callback) {
        bt.send('get_crontab_find', 'crontab/get_crontab_find', { id: id }, function(rdata) {
            if (callback) callback(rdata);
        })
    }

}


bt.config = {
    close_panel: function(callback) {
        layer.confirm(lan.config.close_panel_msg, {
            title: lan.config.close_panel_title,
            closeBtn: 2,
            icon: 13,
            cancel: function() {
                if (callback) callback(false);
            }
        }, function() {
            loading = bt.load(lan.public.the);
            bt.send('ClosePanel', 'config/ClosePanel', {}, function(rdata) {
                loading.close();
                if (callback) callback(rdata);
            })
        }, function() {
            if (callback) callback(false);
        });
    },
    set_auto_update: function(callback) {
        loading = bt.load(lan.public.the);
        bt.send('AutoUpdatePanel', 'config/AutoUpdatePanel', {}, function(rdata) {
            loading.close();
            bt.msg(rdata);
            if (callback) callback(rdata);
        })
    },
    sync_data: function(callback) {
        var loadT = bt.load(lan.config.config_sync);
        bt.send('syncDate', 'config/syncDate', {}, function(rdata) {
            loadT.close();
            bt.msg(rdata);
            if (callback) callback(rdata);
        });
    },
    save_config: function(data, callback) {
        loading = bt.load(lan.config.config_save);
        bt.send('setPanel', 'config/setPanel', data, function(rdata) {
            loading.close();
            bt.msg(rdata);
            if (callback) callback(rdata);
        });
    },
    set_template: function(template, callback) {
        var loadT = bt.load(lan.public.the);
        bt.send('SetTemplates', 'config/SetTemplates', { templates: template }, function(rdata) {
            loadT.close();
            bt.msg(rdata);
            if (callback) callback(rdata);
        });
    },
    set_panel_ssl: function(status, callback) {
        var msg = status ? lan.config.ssl_close_msg : '<a style="font-weight: bolder;font-size: 16px;">' + lan.config.ssl_open_ps + '</a><li style="margin-top: 12px;color:red;">' + lan.config.ssl_open_ps_1 + '</li><li>' + lan.config.ssl_open_ps_2 + '</li><li>' + lan.config.ssl_open_ps_3 + '</li><p style="margin-top: 10px;"><input type="checkbox" id="checkSSL" /><label style="font-weight: 400;margin: -1px 5px 0px;" for="checkSSL">' + lan.config.ssl_open_ps_4 + '</label><a target="_blank" class="btlink" href="https://www.bt.cn/bbs/thread-4689-1-1.html" style="float: right;">' + lan.config.ssl_open_ps_5 + '</a></p>';
        layer.confirm(msg, {
            title: lan.config.ssl_title,
            closeBtn: 2,
            icon: 3,
            area: '550px',
            cancel: function() {
                if (callback) {
                    if (status == 0) {
                        callback(false);
                    } else {
                        callback(true);
                    }
                }
            }
        }, function() {
            if (window.location.protocol.indexOf('https') == -1) {
                if (!$("#checkSSL").prop('checked')) {
                    bt.msg({ msg: lan.config.ssl_ps, icon: 2 });
                    if (callback) callback(false);
                }
            }
            var loadT = bt.load(lan.config.ssl_msg);
            bt.send('SetPanelSSL', 'config/SetPanelSSL', {}, function(rdata) {
                loadT.close();
                bt.msg(rdata);
                if (callback) callback(rdata);
            })
        }, function() {
            if (callback) {
                if (status == 0) {
                    callback(false);
                } else {
                    callback(true);
                }
            }
        });
    },
    get_panel_ssl: function() {
        _this = this;
        loading = bt.load(lan.public_backup.get_cert);
        bt.send('GetPanelSSL', 'config/GetPanelSSL', {}, function(cert) {
            loading.close();
            var certBody = '<div class="tab-con">\
				<div class="myKeyCon ptb15">\
					<div class="ssl-con-key pull-left mr20">' + lan.public_backup.key + '(KEY)<br>\
						<textarea id="key" class="bt-input-text">' + cert.privateKey + '</textarea>\
					</div>\
					<div class="ssl-con-key pull-left">' + lan.public_backup.cret_format + '<br>\
						<textarea id="csr" class="bt-input-text">' + cert.certPem + '</textarea>\
					</div>\
					<div class="ssl-btn pull-left mtb15" style="width:100%">\
						<button class="btn btn-success btn-sm" id="btn_submit">' + lan.public_backup.save + '</button>\
					</div>\
				</div>\
				<ul class="help-info-text c7 pull-left">\
					<li>' + lan.public_backup.cret_help + '<a href="http://www.bt.cn/bbs/thread-704-1-1.html" class="btlink" target="_blank">[' + lan.public_backup.help + ']</a>。</li>\
					<li>' + lan.public_backup.cret_err + '</li><li>' + lan.public_backup.pem_format + '</li>\
				</ul>\
			</div>'
            bt.open({
                type: 1,
                area: "600px",
                title: lan.public_backup.custom_panel_set,
                closeBtn: 2,
                shift: 5,
                shadeClose: false,
                content: certBody
            });

            $("#btn_submit").click(function() {
                key = $('#key').val();
                csr = $('#csr').val();
                _this.set_panel_ssl({ privateKey: key, certPem: csr });
            })
        })
    },
    set_panel_ssl: function(data, callback) {
        var loadT = bt.load(lan.config.ssl_msg);
        bt.send('SavePanelSSL', 'config/SavePanelSSL', data, function(rdata) {
            loadT.close();
            bt.msg(rdata);
            if (callback) callback(rdata);
        })
    },
    set_username: function(type) {
        if (type == 1) {
            if (p1 == "" || p1.length < 3) {
                bt.msg({ msg: lan.bt.user_len, icon: 2 })
                return;
            }
            if (p1 != p2) {
                bt.msg({ msg: lan.bt.user_err_re, icon: 2 })
                return;
            }
            var checks = ['admin', 'root', 'admin123', '123456'];
            if ($.inArray(p1, checks)) {
                bt.msg({ msg: lan.public_backup.usually_user_ban, icon: 2 })
                return;
            }
            bt.send('setUsername', 'config/setUsername', { username1: p1, username2: p2 }, function(rdata) {
                if (rdata.status) {
                    layer.closeAll();
                    $("input[name='username_']").val(p1)
                }
                bt.msg(rdata);
            })
            return;
        }
        bt.open({
            type: 1,
            area: "290px",
            title: lan.bt.user_title,
            closeBtn: 2,
            shift: 5,
            shadeClose: false,
             content: "<div class='bt-form pd20 pb70'><div class='line'><span class='tname' style='width:100px;'>" + lan.bt.user + "</span><div class='info-r' style='margin-left:100px;'><input class='bt-input-text' type='text' name='password1' id='p1' value='' placeholder='" + lan.bt.user_new + "' style='width:100%'/></div></div><div class='line'><span class='tname' style='width:100px;'>" + lan.bt.pass_re + "</span><div class='info-r' style='margin-left:100px;'><input class='bt-input-text' type='text' name='password2' id='p2' value='' placeholder='" + lan.bt.pass_re_title + "' style='width:100%'/></div></div><div class='bt-form-submit-btn'><button type='button' class='btn btn-danger btn-sm' onclick=\"layer.closeAll()\">" + lan.public.close + "</button> <button type='button' class='btn btn-success btn-sm' onclick=\"bt.config.set_username(1)\">" + lan.public.edit + "</button></div></div>"
        })
    },
    set_password: function(type) {
        if (type == 1) {
            p1 = $("#p1").val();
            p2 = $("#p2").val();
            if (p1 == "" || p1.length < 8) {
                bt.msg({ msg: lan.bt.pass_err_len, icon: 2 })
                return
            }

            //准备弱口令匹配元素
            var checks = ['admin888', '123123123', '12345678', '45678910', '87654321', 'asdfghjkl', 'password', 'qwerqwer'];
            pchecks = 'abcdefghijklmnopqrstuvwxyz1234567890';
            for (var i = 0; i < pchecks.length; i++) {
                checks.push(pchecks[i] + pchecks[i] + pchecks[i] + pchecks[i] + pchecks[i] + pchecks[i] + pchecks[i] + pchecks[i]);
            }

            //检查弱口令
            cps = p1.toLowerCase();
            var isError = "";
            for (var i = 0; i < checks.length; i++) {
                if (cps == checks[i]) {
                    isError += '[' + checks[i] + '] ';
                }
            }
            if (isError != "") {
                bt.msg({ msg: lan.bt.pass_err + isError, icon: 2 })
                return;
            }

            if (p1 != p2) {
                bt.msg({ msg: lan.bt.pass_err_re, icon: 2 })
                return
            }
            bt.send('setPassword', 'config/setPassword', { password1: p1, password2: p2 }, function(rdata) {
                layer.closeAll();
                bt.msg(rdata);
            })
            return
        }
        layer.open({
            type: 1,
            area: "290px",
            title: lan.bt.pass_title,
            closeBtn: 2,
            shift: 5,
            shadeClose: false,
            content: "<div class='bt-form pd20 pb70'><div class='line'><span class='tname'>" + lan.public.pass + "</span><div class='info-r'><input class='bt-input-text' type='text' name='password1' id='p1' value='' placeholder='" + lan.bt.pass_new_title + "' style='width:100%'/></div></div><div class='line'><span class='tname'>" + lan.bt.pass_re + "</span><div class='info-r'><input class='bt-input-text' type='text' name='password2' id='p2' value='' placeholder='" + lan.bt.pass_re_title + "' style='width:100%' /></div></div><div class='bt-form-submit-btn'><span style='float: left;' title='" + lan.bt.pass_rep + "' class='btn btn-default btn-sm' onclick='randPwd(10)'>" + lan.bt.pass_rep_btn + "</span><button type='button' class='btn btn-danger btn-sm' onclick=\"layer.closeAll()\">" + lan.public.close + "</button> <button type='button' class='btn btn-success btn-sm' onclick=\"bt.config.set_password(1)\">" + lan.public.edit + "</button></div></div>"
        });
    }
}

bt.system = {
    get_total: function(callback) {
        bt.send('GetSystemTotal', 'system/GetSystemTotal', {}, function(rdata) {
            if (callback) callback(rdata);
        })
    },
    get_net: function(callback) {
        bt.send('GetNetWork', 'system/GetNetWork', {}, function(rdata) {
            if (callback) callback(rdata);
        })
    },
    get_disk_list: function(callback) {
        bt.send('GetDiskInfo', 'system/GetDiskInfo', {}, function(rdata) {
            if (callback) callback(rdata);
        })
    },
    re_memory: function(callback) {
        bt.send('ReMemory', 'system/ReMemory', {}, function(rdata) {
            if (callback) callback(rdata);
        })
    },
    check_update: function(callback, check) {
        var data = {};
        if (check == undefined) data = { check: true };
        if (check === false) data = {}
        if (check) var load = bt.load(lan.index.update_get);
        bt.send('UpdatePanel', 'ajax/UpdatePanel', data, function(rdata) {
            if (check) load.close();
            if (callback) callback(rdata);
        })
    },
    to_update: function(callback) {
        var load = bt.load(lan.index.update_the);
        bt.send('UpdatePanel', 'ajax/UpdatePanel', { toUpdate: 'yes' }, function(rdata) {
            load.close();
            if (callback) callback(rdata);
        })
    },
    reload_panel: function(callback) {
        bt.send('ReWeb', 'system/ReWeb', {}, function(rdata) {
            if (callback) callback(rdata);
        })
    },
    rep_panel: function(callback) {
        var loading = bt.load(lan.index.rep_panel_the)
        $.ajax({
            type: 'POST',
            url: 'system?action=RepPanel',
            error: function (err) {
                setTimeout(() => {
                    loading.close();
                    bt.system.reload_panel(function () {
                        location.reload();
                    });
                }, 1000 * 60 * 5);
            },
            success: function (rdata) {
                loading.close();
                if (rdata) {
                    if (callback) callback({ status: rdata, msg: lan.index.rep_panel_ok });
                    bt.system.reload_panel();
                }
            }
        });
    },
    get_warning: function(callback) {
        bt.send('GetWarning', 'ajax/GetWarning', {}, function(rdata) {
            if (callback) callback(rdata);
        })
    },
    root_reload: function(callback) {
        bt.send('RestartServer', 'system/RestartServer', {}, function(rdata) {
            if (callback) callback(rdata);
        })
    }
}

bt.control = {
    get_status: function(callback) {
        loading = bt.load(lan.public.read);
        bt.send('GetControl', 'control/SetControl', { type: 1 }, function(rdata) {
            if (callback) callback(rdata);
        })
    },
    set_control: function(type, day, callback) {
        loadT = bt.load(lan.public.the);
        bt.send('SetControl', 'config/SetControl', { type: type, day: day }, function(rdata) {
            loadT.close();
            bt.msg(rdata);
            if (callback) callback(rdata);
        })
    },
    clear_control: function(callback) {
        bt.confirm({ msg: lan.control.close_log_msg, title: lan.control.close_log }, function() {
            loadT = bt.load(lan.public.the);
            bt.send('SetControl', 'config/SetControl', { type: 'del' }, function(rdata) {
                loadT.close();
                bt.msg(rdata);
                if (callback) callback(rdata);
            })
        })
    },
    get_data: function(type, start, end, callback) {
        action = '';
        switch (type) {
            case 'cpu': //cpu和内存一起获取
                action = 'GetCpuIo';
                break;
            case 'disk':
                action = 'GetDiskIo';
                break;
            case 'net':
                action = 'GetNetWorkIo';
                break;
            case 'load':
                action = 'get_load_average';
                break;
        }
        if (!action) bt.msg(lan.get('lack_param', 'type'));
        bt.send(action, 'ajax/' + action, { start: start, end: end }, function(rdata) {
            if (callback) callback(rdata, type);
        })
    },
    format_option: function(obj, type) {
        option = {
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'cross'
                },
                formatter: obj.formatter
            },
            xAxis: {
                type: 'category',
                boundaryGap: false,
                data: obj.tData,
                axisLine: {
                    lineStyle: {
                        color: "#666"
                    }
                }
            },
            yAxis: {
                type: 'value',
                name: obj.unit,
                boundaryGap: [0, '100%'],
                min: 0,
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
            },
            dataZoom: [{
                type: 'inside',
                start: 0,
                zoomLock: true
            }, {
                start: 0,
                handleIcon: 'M10.7,11.9v-1.3H9.3v1.3c-4.9,0.3-8.8,4.4-8.8,9.4c0,5,3.9,9.1,8.8,9.4v1.3h1.3v-1.3c4.9-0.3,8.8-4.4,8.8-9.4C19.5,16.3,15.6,12.2,10.7,11.9z M13.3,24.4H6.7V23h6.6V24.4z M13.3,19.6H6.7v-1.4h6.6V19.6z',
                handleSize: '80%',
                handleStyle: {
                    color: '#fff',
                    shadowBlur: 3,
                    shadowColor: 'rgba(0, 0, 0, 0.6)',
                    shadowOffsetX: 2,
                    shadowOffsetY: 2
                }
            }],
            series: []
        };
        if (obj.legend) option.legend = obj.legend;
        if (obj.dataZoom) option.dataZoom = obj.dataZoom;

        for (var i = 0; i < obj.list.length; i++) {
            var item = obj.list[i];
            series = {
                name: item.name,
                type: item.type ? item.type : 'line',
                smooth: item.smooth ? item.smooth : true,
                symbol: item.symbol ? item.symbol : 'none',
                showSymbol: item.showSymbol ? item.showSymbol : false,
                sampling: item.sampling ? item.sampling : 'average',
                areaStyle: item.areaStyle ? item.areaStyle : {},
                lineStyle: item.lineStyle ? item.lineStyle : {},
                itemStyle: item.itemStyle ? item.itemStyle : { normal: { color: 'rgb(0, 153, 238)' } },
                symbolSize: 6,
                symbol: 'circle',
                data: item.data
            }
            option.series.push(series);
        }
        return option;
    }
}



bt.firewall = {
    get_log_list: function(page, search, callback) {
        if (page == undefined) page = 1
        search = search == undefined ? '' : search;
        var order = bt.get_cookie('order') ? '&order=' + bt.get_cookie('order') : '';

        var data = 'tojs=firewall.get_log_list&table=logs&limit=10&p=' + page + '&search=' + search + order;
        bt.pub.get_data(data, function(rdata) {
            if (callback) callback(rdata);
        })
    },
    get_list: function(page, search, callback) {
        if (page == undefined) page = 1
        search = search == undefined ? '' : search;
        var order = bt.get_cookie('order') ? '&order=' + bt.get_cookie('order') : '';

        var data = 'tojs=firewall.get_list&table=firewall&limit=10&p=' + page + '&search=' + search + order;
        bt.pub.get_data(data, function(rdata) {
            if (callback) callback(rdata);
        })
    },
    get_logs_size: function(callback) {
        if (bt.os == 'Linux') {
            bt.files.get_dir_size('/www/wwwlogs', function(rdata) {
                if (callback) callback(rdata);
            })
        }
    },
    get_ssh_info: function(callback) {
        bt.send('GetSshInfo', 'firewall/GetSshInfo', {}, function(rdata) {
            if (callback) callback(rdata);
        })
    },
    set_mstsc: function(port, callback) {
        bt.confirm({ msg: lan.firewall.ssh_port_msg, title: lan.firewall.ssh_port_title }, function() {
            loading = bt.load(lan.public.the);
            bt.send('SetSshPort', 'firewall/SetSshPort', { port: port }, function(rdata) {
                loading.close();
                bt.msg(rdata);
                if (callback) callback(rdata);
            })
        })
    },
    ping: function(status, callback) {
        var msg = status == 0 ? lan.firewall.ping_msg : lan.firewall.ping_un_msg;
        layer.confirm(msg, {
            closeBtn: 2,
            title: lan.firewall.ping_title,
            cancel: function() {
                if (callback) callback(-1); //取消
            }
        }, function() {
            loading = bt.load(lan.public.the);
            bt.send('SetPing', 'firewall/SetPing', { status: status }, function(rdata) {
                loading.close();
                if (callback) callback(rdata);
            })
        }, function() {
            if (callback) callback(-1); //关闭
        })
    },
    set_mstsc_status: function(status, callback) {
        var msg = status == 1 ? lan.firewall.ssh_off_msg : lan.firewall.ssh_on_msg;
        layer.confirm(msg, {
						icon: 0,
            closeBtn: 2,
            title: lan.public.warning,
            cancel: function() {
                if (callback) callback(-1); //取消
            }
        }, function() {
            loading = bt.load(lan.public.the);
            bt.send('SetSshStatus', 'firewall/SetSshStatus', { status: status }, function(rdata) {
                loading.close();
                if (callback) callback(rdata);
            })
        }, function() {
            if (callback) callback(-1); //关闭
        })
    },
    add_accept_port: function(type, port, ps, callback) {
        var action = "AddDropAddress";
        if (type == 'port') {
            ports = port.split(':');
            if (port.indexOf('-') != -1) ports = port.split('-');
            for (var i = 0; i < ports.length; i++) {
                if (!bt.check_port(ports[i])) {
                    layer.msg(lan.firewall.port_err, { icon: 5 });
                    return;
                }
            }
            action = "AddAcceptPort";
        }

        // if (ps.length < 1) {
        //     layer.msg(lan.firewall.ps_err, { icon: 2 });
        //     return -1;
        // }
        loading = bt.load();
        bt.send(action, 'firewall/' + action, { port: port, type: type, ps: ps }, function(rdata) {
            loading.close();
            if (callback) callback(rdata);
        })
    },
    del_accept_port: function(id, port, callback) {
        var action = "DelDropAddress";
        if (port.indexOf('.') == -1) {
            action = "DelAcceptPort";
        }
        bt.confirm({ msg: lan.get('confirm_del', [port]), title: lan.firewall.del_title }, function(index) {
            var loadT = bt.load(lan.public.the_del);
            bt.send(action, 'firewall/' + action, { id: id, port: port }, function(rdata) {
                loadT.close();
                if (callback) callback(rdata);
            })
        });
    },
    clear_logs_files: function(callback) {
        var loadT = bt.load(lan.firewall.close_the);
        bt.send('CloseLogs', 'files/CloseLogs', {}, function(rdata) {
            if (callback) callback(rdata);
        })
    },
    clear_logs: function(callback) {
        bt.confirm({ msg: lan.firewall.close_log_msg, title: lan.firewall.close_log }, function() {
            var loadT = bt.load(lan.firewall.close_the);
            bt.send('delClose', 'ajax/delClose', {}, function(rdata) {
                loadT.close();
                if (callback) {
                    callback(rdata);
                } else {
                    bt.msg(rdata)
                }
            })
        })
    }
}

bt.soft = {
    SSL_flag : false,
    pub: {
        wxpayTimeId: 0
    },
    php: {
        get_config: function(version, callback) { //获取禁用函数,扩展列表
            // var loading = bt.load();
            bt.send('GetPHPConfig', 'ajax/GetPHPConfig', { version: version }, function(rdata) {
                // loading.close();
                if (callback) callback(rdata);
            })
        },
        get_limit_config: function(version, callback) { //获取超时限制,上传限制
            var loading = bt.load();
            bt.send('get_php_config', 'config/get_php_config', { version: version }, function(rdata) {
                loading.close();
                if (callback) callback(rdata);
            })
        },
        get_php_config: function(version, callback) {
            var loading = bt.load();
            bt.send('GetPHPConf', 'config/GetPHPConf', { version: version }, function(rdata) {
                loading.close();
                if (callback) callback(rdata);
            })
        },
        install_php_lib: function(version, name, title, callback) {
            bt.confirm({ msg: lan.soft.php_ext_install_confirm.replace('{1}', name), title: lan.public_backup.install + '【' + name + '】' }, function() {
                name = name.toLowerCase();
                var loadT = bt.load(lan.soft.add_install);
                bt.send('InstallSoft', 'files/InstallSoft', { name: name, version: version, type: "1" }, function(rdata) {
                    loadT.close();
                    if (callback) callback(rdata);
                    bt.msg(rdata);
                });
                fly("bi-btn");
            });
        },
        un_install_php_lib: function(version, name, title, callback) {
            bt.confirm({ msg: lan.soft.php_ext_uninstall_confirm.replace('{1}', name), title: lan.public_backup.uninstall + '【' + name + '】' }, function() {
                name = name.toLowerCase();
                var data = 'name=' + name + '&version=' + version;
                var loadT = bt.load();
                bt.send('UninstallSoft', 'files/UninstallSoft', { name: name, version: version }, function(rdata) {
                    loadT.close();
                    if (callback) callback(rdata);
                    bt.msg(rdata);
                });
            });
        },
        set_upload_max: function(version, max, callback) {
            var loadT = bt.load(lan.soft.the_save);
            bt.send('setPHPMaxSize', 'config/setPHPMaxSize', { version: version, max: max }, function(rdata) {
                loadT.close();
                if (callback) callback(rdata);
            })
        },
        set_php_timeout: function(version, time, callback) {
            var loadT = bt.load(lan.soft.the_save);
            bt.send('setPHPMaxTime', 'config/setPHPMaxTime', { version: version, time: time }, function(rdata) {
                loadT.close();
                if (callback) callback(rdata);
            });
        },
        disable_functions: function(version, fs, callback) {
            var loadT = bt.load();
            bt.send('setPHPDisable', 'config/setPHPDisable', { version: version, disable_functions: fs }, function(rdata) {
                loadT.close();
                if (callback) callback(rdata);
            });
        },
        get_fpm_config: function(version, callback) {
            var loadT = bt.load();
            bt.send('getFpmConfig', 'config/getFpmConfig', { version: version }, function(rdata) {
                loadT.close();
                if (callback) callback(rdata);
            })
        },
        set_fpm_config: function(version, data, callback) {
            var loadT = bt.load();
            data.version = version;
            bt.send('setFpmConfig', 'config/setFpmConfig', data, function(rdata) {
                loadT.close();
                if (callback) callback(rdata);
            })
        },
        get_php_status: function(version, callback) {
            var loadT = bt.load();
            bt.send('GetPHPStatus', 'ajax/GetPHPStatus', { version: version }, function(rdata) {
                loadT.close();
                if (callback) callback(rdata);
            })
        },
        // 获取PHP_session
        get_php_session: function(version, callback) {
            var loadT = bt.load();
            bt.send('GetSessionConf', 'config/GetSessionConf', { version: version }, function(res) {
                loadT.close();
                if (callback) callback(res);
            });
        },
        // 设置PHP_session文件
        set_php_session: function(obj, callback) {
            var loadT = bt.load();
            bt.send('SetSessionConf', 'config/SetSessionConf', obj, function(res) {
                loadT.close();
                if (callback) callback(res);
            });
        },
        // 获取PHP_session清理信息
        get_session_count: function(callback) {
            var loadT = bt.load();
            bt.send('GetSessionCount', 'config/GetSessionCount', {}, function(res) {
                loadT.close();
                if (callback) callback(res);
            });
        },
        // 清理php_session
        clear_session_count: function(obj, callback) {
            bt.confirm({ msg: obj.msg, title: obj.title }, function() {
                var loadT = bt.load();
                bt.send('DelOldSession', 'config/DelOldSession', {}, function(res) {
                    loadT.close();
                    if (callback) callback(res);
                })
            });
        },
        get_fpm_logs: function(version, callback) {
            var loadT = bt.load();
            bt.send('GetFpmLogs', 'ajax/GetFpmLogs', { version: version }, function(logs) {
                loadT.close();
                if (logs.status !== true) {
                    logs.msg = '';
                }
                if (logs.msg == '') logs.msg = lan.public_backup.no_fpm_log;
                if (callback) callback(logs);
            })
        },
        get_slow_logs: function(version, callback) {
            var loadT = bt.load();
            bt.send('GetFpmSlowLogs', 'ajax/GetFpmSlowLogs', { version: version }, function(logs) {
                loadT.close();
                if (logs.status !== true) {
                    logs.msg = '';
                }
                if (logs.msg == '') logs.msg = lan.public_backup.no_slow_log;
                if (callback) callback(logs);
            })
        }
    },
    redis: {
        get_redis_status: function(callback) {
            var loadT = bt.load();
            bt.send('GetRedisStatus', 'ajax/GetRedisStatus', {}, function(rdata) {
                loadT.close();
                if (callback) callback(rdata);
            });
        }
    },
    pro: {
			conver_unit: function(name) {
					var unit = '';
					switch (name) {
							case "year":
									unit = lan.public_backup.year;
									break;
							case "month":
									unit = lan.public_backup.month;
									break;
							case "day":
									unit = lan.public_backup.day;
									break;
							case "1month":
									unit = lan.public_backup.month;
									break;
							case "3month":
									unit = lan.public_backup.month3;
									break;
							case "6month":
									unit = lan.public_backup.month6;
									break;
							case "1year":
									unit = lan.public_backup.year1;
									break;
							case "2year":
									unit = lan.public_backup.year2;
									break;
							case "3year":
									unit = lan.public_backup.year3;
									break;
							case "1":
									unit = lan.public_backup.month1;
									break;
							case "3":
									unit = lan.public_backup.month3;
									break;
							case "6":
									unit = lan.public_backup.month6;
									break;
							case "12":
									unit = lan.public_backup.year1;
									break;
							case "24":
									unit = lan.public_backup.year2;
									break;
							case "36":
									unit = lan.public_backup.year3;
									break;
							case "999":
									unit = lan.public_backup.permanent;
									break;
					}
					return unit;
			},
			get_product_discount_by: function(product_id, callback) {
				if (product_id) {
					bt.send('get_plugin_price', 'auth/get_plugin_price', { product_id: product_id }, function(rdata) {
						if (callback) callback(rdata)
					})
				} else {
					bt.send('get_product_discount_by', 'auth/get_product_discount_by', {}, function(rdata) {
						if (callback) callback(rdata)
					})
				}
			},
			get_plugin_coupon: function(pid, callback) {
				bt.send('check_pay_status', 'auth/check_pay_status', { id: pid }, function(rdata) {
					if (callback) callback(rdata);
				})
			},
			get_re_order_status: function(callback) {
				bt.send('get_re_order_status', 'auth/get_re_order_status', {}, function(rdata) {
					if (callback) callback(rdata);
				})
			},
			get_voucher: function(pid, callback) {
					if (pid) {
							bt.send('get_voucher_plugin', 'auth/get_voucher_plugin', { pid: pid }, function(rdata) {
									if (callback) callback(rdata);
							})
					} else {
							bt.send('get_voucher', 'auth/get_voucher', {}, function(rdata) {
									if (callback) callback(rdata);
							})
					}
			},
				get_check_out_info: function(data, callback) {
					bt.send('get_stripe_session_id', 'auth/get_stripe_session_id', data, function(rdata) {
							if (callback) callback(rdata);
					})
			},
			create_order_voucher: function(pid, code, coupon_id, cycle, cycle_unit, charge_type,callback) {
					var loading = bt.load();
					if (pid) {
							bt.send('create_order_voucher_plugin', 'auth/create_order_voucher_plugin', { pid: pid, coupon_id:coupon_id, cycle:cycle, cycle_unit:cycle_unit, charge_type:charge_type}, function(rdata) {
									loading.close();
									if (callback) callback(rdata);
									bt.msg(rdata);
							})
					} else {
							bt.send('create_order_voucher', 'auth/create_order_voucher', { code: code }, function(rdata) {
									loading.close();
									if (callback) {
											callback(rdata);
									} else {
											bt.soft.pro.update();
									}
							})
					}
    	},
      create_order: function(data, callback) {
        if (data.pid) {
          // var loadT = bt.load("Getting product information!");
          bt.soft.get_panel_ssl_status(function (res) {
            // loadT.close()
            if (res.status) {
              // var _cycle_unit = $('#libPay-content .li-con .active  span').attr("data-unit"),
              // _pay_channel = $('#libPay-mode .pay-cycle-btn span').text().indexOf('Stripe') > -1?'2':'10'
              // requestNmae = data.serial_no ? 'renew_product_auth' : 'get_buy_code';
							var requestNmae = 'get_buy_code';
              if(!data.serial_no) {
                data.charge_type = 1
              }else{
                data.pay_channel = 2
              }
              bt.send(requestNmae, 'auth/' + requestNmae, data, function (rdata) {
                // loadT.close()
                if (callback) callback(rdata);
              })
            } else {
              $('#libPay-content').empty()
              $('.libPay-mask').hide();
              $('#libPay-pay').empty().append('\
							<div style="font-size: 16px; position: relative; top: 25px;">\
								<div style="font-weight: bold;">Purchase on the panel:</div>\
								<ul class="help-info-text" style="margin-top: 10px; font-size: 14px;">\
									<li>You need to open the panel SSL</li>\
								</ul>\
								<div style="margin-top: 20px; font-weight: bold;">Purchase on the official website: </div>\
								<ul class="help-info-text" style="margin-top: 10px; font-size: 14px;">\
									<li>No need to open panel SSL</li>\
									<li>You can purchase multiple licenses at the same time and get higher discounts</li>\
								</ul>\
							</div>\
              <div class="lib-price-box text-center">\
								<button type="button" id="turn_on_ssl" style="margin-top:50px" class="btn btn-success ">Turn on SSL</button>\
							</div>');
              $('#turn_on_ssl').on('click', function (e) {
                setPanelSSL()
              })
              return false;
            }
          });
        } else {
          bt.send('create_order', 'auth/create_order', {
            cycle: data.cycle
          }, function (rdata) {
            if (callback) callback(rdata);
          })
        }
      }
    },
    updata_commercial_view:function(){
		layer.closeAll();
		var html = '<div class="business-edition">\
			<div class="price-compare-item">\
				<div class="price-header">Pro<san class="recommend-tips"></span></div>\
				<div class="title-wrap">\
					<p class="title-info">推荐5人以上或企事业单位购买</p>\
				</div>\
				<div class="title-desc">\
					<p>包含所有<b>专业版</b>功能和：</p>\
					<p>1、提供在线客服工单协助</p>\
					<p>2、多用户管理插件（仅可查看日志）</p>\
					<p>3、后期还会有10+企业版专用插件</p>\
					<p>4、官方跟进响应的QQ群（需年付）</p>\
					<p>4、官方跟进响应的QQ群（需年付）</p>\
					<p>5、不定期线上运维培训（需年付）</p>\
				</div>\
				<div class="price-wrap">\
					<div class="month">\
						<span class="price-unit">￥</span>\
						<span class="price-value">148</span>\
						<span class="price-ext">/月</span>\
					</div>\
					<div class="div-line"></div>\
					<div class="year">\
						<span class="price-unit">￥</span>\
						<span class="price-value">999</span>\
						<span class="price-ext">/年</span>\
					</div>\
				</div>\
				<button class="btn-price" data-type="ltd">Upgrade</button>\
			</div>\
		</div>';
		layer.open({
			type: 1
			,closeBtn:2
			,area: '500px'
			,title: lan.public_backup.up_pro_use_allplug_free
			,shade: 0.6
			,anim: 0
			,content:html,
			success:function(layero,index){
				$('.btn-price').click(function(){
					var _type = $(this).attr('data-type');
					if(_type == 'pro'){
						bt.soft.updata_pro();
						layer.close(index);
					}else{
						bt.soft.updata_ltd();
						layer.close(index);
					}
				})
			}
		})
	},
	get_index_renew:function(){
	 	bt.soft.get_product_renew(function(res){
            var html = $('<div><div>');
            if(res.length >0){
                bt.soft.each(res,function(index,item){
                    html.append($('<p><span class="glyphicon glyphicon-alert" style="color: #f39c12; margin-right: 10px;"></span>' + item.msg +'&nbsp;&nbsp;&nbsp;&nbsp;<a href="javascript:;" class="set_messages_status" style="color:#777">[ 忽略提示 ]</a></p>').data(item))
                });
                $('#messageError').show().html(html);
                $('.set_messages_status').click(function(){
                    var data = $(this).parent().data(),that = this;
                    bt.soft.set_product_renew_status({id:data.id,state:0},function(rdata){
                        if(!res.status){
                            $(that).parent().remove();
                        }
                        bt.msg(rdata);
                    });
                })
            }

	 	});
	},
	// 获取产品续费状态
	get_product_renew:function(callback){
	    $.get('/message/get_messages',function(res){
	        if(res.status === false){
	            layer.msg(res.msg,{icon:2});
	            return false;
	        }
            if(callback) callback(res)
        });
	},
	//获取产品ssl
	get_panel_ssl_status:function(callback){
	    $.post('/config?action=get_panel_ssl_status',function(res){
            if(callback) callback(res)
        });
	},
  set_product_renew_status: function (data, callback) {
    $.post('/message/status_message', {id: data.id, state: data.state}, function (res) {
      if (res.status === false) {
        layer.msg(res.msg, {icon: 2});
        return false;
      }
      if (callback) callback(res)
    });
  },
  // 产品支付视图(配置参数)
  product_pay_view: function (config) {
		if (!bt.get_cookie('bt_user_info')) {
      bt.pub.bind_btname(function () {
        window.location.reload();
      });
      return false;
    }

		if (config.renew === -1) config.renew = false
    if (typeof config == "string") config = JSON.parse(config);

    config = $.extend({
      plugin: null,
      renew: null,
      active: '',
      type: '',
      pro: parseInt(bt.get_cookie('pro_end')) || -1,
      ltd: parseInt(bt.get_cookie('ltd_end')) || -1
    }, config);

		var totalNum = config.totalNum ? config.totalNum : '';
		if (totalNum) {
			bt.set_cookie('pay_source', parseInt(totalNum));
		}

		var that = this;

    bt.open({
      type: 1,
			title: false,
			skin: 'libPay-view',
      area: ['1024px', '600px'],
      shadeClose: false,
      content: '\
			<div class="libPay-content-box pro">\
				<div class="libPay-product-introduce">\
					<div class="pro-left-introduce pro">\
						<div class="pro-left-title">\
							<div></div>\
							<span></span>\
						</div>\
						<div class="pro-left-list">\
							<div class="pro-left-list-title"></div>\
							<div class="pro-left-list-content"></div>\
						</div>\
						<div class="pro-price-herf">\
							<a class="privilege_contrast" href="https://aapanel.com/new/pricing.html" target="_blank" rel="noreferer noopener">Feature contrast</a>\
						</div>\
					</div>\
				</div>\
				<div class="libPay-product-content">\
					<div class="libPay-menu"></div>\
					<div id="pay_product_view">\
						<div class="libPay-layer-item aShow">\
							<div class="libPay-line-item proTname" style="margin-bottom: 20px">Choose your plan</div>\
							<div class="libPay-line-item proP" id="libPay-theme-price">\
								<div class="switch-cycle-left hide"><span class="glyphicon glyphicon-chevron-left"></span></div>\
								<ul class="pay-pro-cycle"></ul>\
								<div class="switch-cycle-right hide"><span class="glyphicon glyphicon-chevron-right"></span>\
							</div>\
						</div>\
						<div class="libPay-line-item libPay-mode">\
							<div class="libPay-qcode-left">\
								<div class="pay-radio-type">\
									<div class="pay-type-btn active" data-condition="stripe">\
										<label class="pay-type-label"><span class="pay-radio-tit">Stripe</span></label>\
									</div>\
									<div class="pay-type-btn" data-condition="paypal">\
										<label class="pay-type-label"><span class="pay-radio-tit">Paypal</span></label>\
									</div>\
									<div class="pay-type-btn" data-condition="voucher">\
										<label class="pay-type-label"><span class="pay-radio-tit">Voucher</span></label>\
									</div>\
									<div class="pay-type-btn" data-condition="authorization">\
										<label class="pay-type-label"><span class="pay-radio-tit">Authorization</span></label>\
									</div>\
									<div class="pay-type-other"></div>\
								</div>\
							</div>\
							<div class="libPay-qcode-right">\
								<div class="libPay-qcode-right-head"></div>\
								<div class="libPay-qcode-item">\
									<div class="cloading">Loading, please wait!</div>\
									<div class="pay-box">\
										<div class="userinfo">\
											<div class="info_label">Account: </div>\
											<div class="info_value">--</div>\
											<a class="btlink" href="javascript:;" style="text-decoration: underline">Change</a>\
										</div>\
										<div class="pay-price">\
											<span class="price-label">Total: </span>\
											<span class="org_price">$0</span>\
											<span>, After discount </span>\
											<span class="libPayTotal"><span style="font-size: 18px; margin-left: 4px; margin-right: 2px;">$</span>0</span>\
											<span class="libPayCycle">/1 year</span>\
										</div>\
										<div class="pay-subscription hide">\
											<input type="checkbox" name="subscription" checked="checked" />\
											<span>Pay for subscription</span>\
											<span class="org-price">$0/year</span>\
											<span class="first-price">\
												<span class="symbol">$</span>\
												<span class="num">0</span>\
											</span>\
											<span class="cycle-unit">/first year</span>\
											<a href="javascript:;" class="bt-ico-ask">?</a>\
										</div>\
										<button class="btn btn-success btn-pay" id="checkout-button">Pay Now</button>\
									</div>\
								</div>\
								<div class="libPay-qcode-item hide">\
									<div class="pay-box">\
										<div class="userinfo">\
											<div class="info_label">Account: </div>\
											<div class="info_value">--</div>\
											<a class="btlink" href="javascript:;" style="text-decoration: underline">Change</a>\
										</div>\
										<div class="pay-price">\
											<span class="price-label">Total: </span>\
											<span class="org_price">$0</span>\
											<span>, After discount </span>\
											<span class="libPayTotal"><span style="font-size: 18px; margin-left: 4px; margin-right: 2px;">$</span>0</span>\
											<span class="libPayCycle">/1 year</span>\
										</div>\
										<div id="paypal-button-container" style="width: 240px; height: 35px; margin: 20px auto 0;"></div>\
									</div>\
								</div>\
								<div class="libPay-qcode-item hide">\
									<div class="li-tit c4">Vouchers</div>\
									<ul class="pay-btn-group voucher-group"></ul>\
									<div class="text-center">\
										<button class="btn btn-success btn-sm f16" id="use-voucher" style="width: 200px; height: 40px;">Pay</button>\
									</div>\
								</div>\
								<div class="libPay-qcode-item hide">\
									<div class="li-tit c4">Authorization information</div>\
									<ul class="pay-btn-group auth-group"></ul>\
									<div class="text-center">\
										<button class="btn btn-success btn-sm f16" id="use-auth" style="width: 200px; height: 40px;">Authorization</button>\
									</div>\
								</div>\
							</div>\
						</div>\
					</div>\
				</div>\
			</div>',
			end: function () {
				bt.clear_cookie('pay_source');
			},
      success: function ($layer, index) {
        $.getScript('https://js.stripe.com/v3/');

				var layerThat = this;

				layerThat.renderUserInfo();
				layerThat.renderProductMenu();

				var init = () => {
					var removeLoad =  layerThat.addLoading('.libPay-layer-item');
					layerThat.renderFeature();
					layerThat.renderAuthList(function (rdata) {
						if (rdata.length > 0) {
							cutTab('authorization');
							layerThat.renderProductPrice(function () {
								removeLoad()
							});
						} else {
							layerThat.renderVoucher(function (rdata) {
								if (rdata.length > 0) {
									cutTab('voucher');
								}
								layerThat.renderProductPrice(function () {
									removeLoad()
								});
							});
						}
					});
				}

				init();

				$('.switch-cycle-right').click(function () {
					var num = $(this).prev().children().length;
					var width = 196;
					var remainder =  num % 4; // 获取余数
					$(this).prev().css('transform','translateX(-'+(remainder * width ) + 'px)')
					$('.switch-cycle-left').removeClass('hide')
					$('#libPay-theme-price').css('padding-left','30px')
					$(this).addClass('hide')
				});

				$('.switch-cycle-left').click(function (ev) {
					if(bt.del_seven_coupon){
						var $children = $('.pay-pro-cycle').children()
						if($($children[0]).data('data').nums.length == 1){
							$($children[0]).remove()
							bt.del_seven_coupon = false
						}
					}
					$('#libPay-theme-price').removeAttr('style')
					$('.switch-cycle-right').removeClass('hide')
					$(this).next().removeAttr('style')
					$(this).addClass('hide')
				});

				$('.pay-btn-group').on('click', 'li', function () {
					$(this).addClass('active').siblings('.active').removeClass('active');
				});
				
				// 切换菜单
				$('.libPay-menu').on('click', '.libPay-menu-type', function () {
					$(this).addClass('active').siblings('.active').removeClass('active');
					init();
				});

				// 产品周期切换
				$('#libPay-theme-price .pay-pro-cycle').on('click', 'li', function () {
					$(this).addClass('active').siblings('.active').removeClass('active');
					var condition = $('.libPay-qcode-left .pay-type-btn.active').data('condition');
					if (condition === 'stripe') {
						layerThat.renderTotalPrice();
					} else if (condition === 'paypal') {
						layerThat.renderPaypal();
					}
				});

				// 点击支付
				$('#checkout-button').click(function () {
					var config = $(this).data('data');
					var loadT = bt.load('Getting the session ID,Please waiting!');
					var stripe = Stripe(config.stripe_publishable_key);
					var subscribe = config.subscription_price > 0 && $('.pay-subscription input').prop('checked') ? 1 : 0;
					that.pro.get_check_out_info({
						order_no: config.order_no,
						subscribe: subscribe
					}, function (res) {
						loadT.close();
						if (res.id) {
							stripe.redirectToCheckout({ sessionId: res.id });
						} else {
							layer.msg('Payment order failed, please contact administrator!', { icon: 2 });
						}
					});
				});

				// 切换tab
				function cutTab(condition) {
					var $el = $('.libPay-qcode-left .pay-type-btn[data-condition="' + condition + '"]');
					var index = $el.index();
					$el.addClass('active').siblings('.active').removeClass('active');
					$('.libPay-qcode-right .libPay-qcode-item').eq(index).removeClass('hide').siblings('.libPay-qcode-item').addClass('hide');
				}

				// 支付方式切换
				$('.libPay-qcode-left .pay-type-btn').click(function () {
					var condition = $(this).data('condition');
					cutTab(condition);

					var condition = $(this).data('condition');
					switch (condition) {
						case 'stripe':
							layerThat.renderTotalPrice();
							break;
						case 'paypal':
							layerThat.renderPaypal();
							break;
						case 'voucher':
							layerThat.renderVoucher();
							break;
						case 'authorization':
							layerThat.renderAuthList();
							break;
					}
				});

				// 切换用户
				$('.libPay-qcode-item .userinfo a').click(function () {
					bt.pub.bind_btname(function () {
						// bt.soft.product_pay_view(config);
						window.location.reload();
					});
				});

				// 使用抵扣卷
				$('#use-voucher').click(function () {
					if ($(this).hasClass('disabled')) return false;

					var data = $('.voucher-group .active').data();
					if (!data.serial_no) {
						layer.msg('No vouchers');
						return false;
					}
					bt.soft.pro.create_order_voucher(data.pid, data.code, data.id, data.cycle, data.cycle_unit, data.charge_type, function (rdata) {
						layer.closeAll();
						bt.set_cookie('force', 1);
						if (soft) soft.flush_cache();
						bt.msg(rdata);
						if (rdata.status) {
							getPaymentStatus();
						}
					});
				});

				// 授权
				$('#use-auth').click(function () {
					if ($(this).hasClass('disabled')) return false;

					var _serial_no = $('.auth-group .active').attr('data-id');
					if (typeof _serial_no == 'undefined') return false;
					var loadU = bt.load('Under licensing!');
					bt.send('auth_activate', 'auth/auth_activate', { serial_no: _serial_no }, function (res) {
						loadU.close();
						if (res) {
							layer.msg(res.msg, { icon: res.status ? 1 : 2 });
							if (res.status) {
								window.location.reload();
							}
						}
					});
				});

				var layerIndex = -1;

				$('.pay-subscription .bt-ico-ask').hover(function () {
					layerIndex = layer.tips('<div>when subscription creation, your authorization will auto generated<br />when subscription renewal, your authorization will auto renewed</div>', $(this), {
						tips: [1, '#999'],
						time: 0,
						area: '410px'
					});
				}, function () {
					layer.close(layerIndex);
				});
      },
			addLoading: function (elem) {
				var $el = $(elem);
				$el.children().addClass('hide');
				if ($el.children('.cloading').length === 0) {
					$el.append('<div class="cloading">Loading, please wait!</div>');
				}
				return function removeLoad () {
					$el.children('.cloading').remove();
					$el.children().removeClass('hide');
				}
			},
			getConfig: function () {
				var data = $('.libPay-menu .libPay-menu-type.active').data();
				return data;
			},
			// 渲染菜单
			renderProductMenu: function () {
				var menus = []
				if (config.plugin) {
					menus.push({
						title: config.name,
						name: config.name,
						ps: 'Plug-in only',
						desc: config.ps,
						pid: config.pid,
						renew: config.renew || false,
						is_pro: false,
						active: (config.pro < 0 && config.ltd < 0) || (config.type == 12 && config.ltd < 0) ? true : false,
					});
				}
				if (
					(((config.pro > 0 || config.pro == -2 || config.ltd < 0) && ((config.ltd > 0 && config.ltd != config.pro) || config.ltd < 0) && config.type != 12) ||
						config.limit == 'pro' ||
						(config.ltd < 0 && config.pro == -1)) &&
					config.type != 12 &&
					((config.ltd < 0 && config.pro > 0) || (config.ltd < 0 && config.pro < 0))
				) {
					menus.push({
						title: 'PRO',
						name: '',
						pid: '100000058',
						ps: 'Recommended',
						renew: config.renew || false,
						is_pro: true,
						active:
							((config.type == 8 && !config.plugin) || config.limit == 'pro' || config.pro > 0 || config.pro == -2) && config.ltd < 0 && (config.ltd == -2 ? (config.pro == -2 ? false : true) : true),
					});
				}

				var $el = null;
				$.each(menus, function (index, item) {
					$el = $('<div class="libPay-menu-type ' + (item.is_pro ? 'lib_pro' : '') + ' ' + (item.active ? 'active' : '') + '">\
						<p>\
							' + (item.is_pro ? '<span class="glyphicon glyphicon-vip" style="margin-right: 8px"></span>' : '') + '<span>' + item.title + '</span>\
						</p>\
						<p>' + item.ps + '</p>\
					</div>').data(item);
					$('.libPay-menu').append($el);
				});
			},
			renderFeature: function () {
				var config = this.getConfig();
				
				if (config.is_pro) {
					$('.pro-left-introduce .pro-left-title>div').html('<span class="glyphicon glyphicon-vip" style="margin-right: 7px"></span><span>' + config.title + '</span>');
					$('.pro-left-introduce .pro-left-title>span').removeClass('hide').html(config.ps);
					$('.pro-left-list-title').text('Pro Feature: ');
					$('.pro-price-herf').removeClass('hide');
					bt.send('get_plugin_remarks', 'auth/get_plugin_remarks', { product_id: '100000058' }, function (rdata) {
						var html = '';
						$.each(rdata.res, function (index, item) {
							html += '<div class="pro-introduce"><span class="glyphicon glyphicon-ok"></span><span>' + item + '</span></div>';
						});
						$('.pro-left-list-content').removeAttr('style').html(html);
					});
				} else {
					$('.pro-left-introduce .pro-left-title>div').html('<span>' + config.title + '</span>');
					$('.pro-left-introduce .pro-left-title>span').addClass('hide').html(config.ps);
					$('.pro-left-list-title').text('Plug-in description: ');
					$('.pro-left-list-content').css({
						'width': '186px',
						'line-height': '23px'
					}).html(config.desc);
					$('.pro-price-herf').addClass('hide');
				}
			},
			// 渲染产品价格
			renderProductPrice: function (callback) {
				var layerThat = this;

				var config = layerThat.getConfig();

				that.get_product_discount_cache(config, function (rdata) {

					if (callback) callback(rdata);

					// 大于4个显示左右切换按钮
					var num = rdata.length;
					if (num > 4) {
						$('.switch-cycle-right').removeClass('hide');
					} else {
						$('.switch-cycle-right,.switch-cycle-left').addClass('hide');
					}

					
					// 遍历渲染产品价格
					var html = '';
					$('#libPay-theme-price .pay-pro-cycle').empty()
					that.each(rdata, function (key, item) {
						var keys = item.cycle;
						var priceByDay = (item.price / ((item.cycle / (item.cycle_unit === 'year' ? 1 : 12)) * 365)).toFixed(2);
						var cycleUnit =  item.cycle  + ' ' + item.cycle_unit + (item.cycle > 1 ? 's' : '')
						
						html = '\
						<li class="pay-cycle-btns '+ (key === 0 ? 'active' : '') + '" data-type="' + keys + '">\
							<div class="pay-head-price">\
								<div class="new-price">\
									<div class="libPrice">$<i>' + (item.price).toFixed(2) + '</i></div>\
									<div class="cycle">/' + cycleUnit + '</div>\
								</div>\
								<p>OP: $' + item.market_price + '</p>\
							</div>\
							<div class="pay-foo-price">As low as $' + priceByDay + '/day</div>\
							' + (item.discount_rate != 1 ? '<em>' + (100 - item.discount_rate * 100) + '% off</em>' : '') + '\
						</li>';
						$('#libPay-theme-price .pay-pro-cycle').append($(html).data($.extend({
							pid: config.pid,
							dom_index: key
						}, item)));
					});

					layerThat.renderTotalPrice();
				});
			},
			// 渲染用户信息
			renderUserInfo: function () {
				var bt_user_info = bt.get_cookie('bt_user_info');
				if (!bt_user_info) {
					bt.pub.get_user_info(function (res) {
						$('.libPay-qcode-right .userinfo .info_value').html(res.data.username);
					});
				} else {
					$('.libPay-qcode-right .userinfo .info_value').html(JSON.parse(bt_user_info).data.username);
				}
			},
			renderEndTime: function () {
				var endTime = null;
				if (!config.is_alone) {
					// 条件：当前为插件
					if (config.plugin) {
						title = (!config.renew ? 'Buy ' : '续费') + config.name;
						ndTime = !config.renew ? config.renew : null;
					} else if (config.pro == -1 && config.ltd == -1) {
						// 条件：专业版和企业版都没有购买过
						title = 'Upgrade to Pro, all plugins are free to use';
					} else if (config.ltd > 0) {
						// 条件：企业版续费
						title = 'Renew ' + (config.name == '' ? '宝塔专业版' : config.name);
						endTime = config.ltd;
					} else if (config.pro > 0 || config.pro == -2) {
						// 条件：专业版续费
						title = 'Renew ' + (config.name == '' ? '宝塔专业版' : config.name);
						endTime = config.pro;
					} else if (config.ltd == -2) {
						title = 'Renew ' + (config.name == '' ? '宝塔专业版' : config.name);
						endTime = config.ltd;
					}
				} else {
					title = (config.ltd > 0 ? '续费' : '购买') + '宝塔企业版';
				}
				if (endTime != null) {
					$('.endTime span').html(endTime > parseInt(new Date().getTime() / 1000) ? bt.format_data(endTime) : '<i style="color:red;font-style:inherit">Expired</i>');
				} else {
					$('.endTime').hide();
				}
			},
			// 渲染总价格
			renderTotalPrice: function () {
				var condition = $('.libPay-qcode-left .pay-type-btn.active').data('condition');
				if (condition !== 'stripe') {
					return;
				}

				var layerThat = this;
				var removeLoad = layerThat.addLoading('.libPay-qcode-item:not(.hide)');
				var config = $('#libPay-theme-price .pay-pro-cycle .active').data();
				var param = { pid: config.pid, cycle: config.cycle, cycle_unit: config.cycle_unit, charge_type: config.charge_type };
				param.source = parseInt(bt.get_cookie('pay_source') || 0);
				if (param.source === 0) {
					if ($('.btpro-gray').length == 1) {
						// 是否免费版
						param.source = 27;
					} else {
						param.source = 28;
					}
				}
				if (!param.pid) delete param.pid;
				if (bt.get_cookie('serial_no') != null) param.serial_no = config.serial_no || bt.get_cookie('serial_no');
				that.pro.create_order(param, function (rdata) {
					removeLoad();
					if (rdata.status === false) {
						bt.set_cookie('force', 1);
						if (soft) soft.flush_cache();
						layer.msg(rdata.msg, { icon: 2 });
						return;
					}

					var cycle = config.cycle + ' ' + config.cycle_unit + (config.cycle > 1 ? 's' : '');
					// var unit = config.num + ' unit' + (config.num > 1 ? 's' : '');
					$('.libPayTotal').html('<span style="font-size: 18px; margin-left: 4px; margin-right: 2px">$</span>' + config.price);
					$('.pay-price .org_price').text('$' + config.market_price + '/' + cycle);
					$('.pay-price .libPayCycle').html('/' + cycle);

					if (config.subscription_price > 0) {
						$('.pay-subscription').removeClass('hide');
						if (config.first_subscription_price > 0) {
							$('.pay-subscription .org-price').removeClass('hide');
							$('.pay-subscription .org-price').text('$' + config.subscription_price + '/' + config.cycle_unit);
							$('.pay-subscription .first-price .num').text(config.first_subscription_price);
						} else {
							$('.pay-subscription .org-price').addClass('hide');
							$('.pay-subscription .first-price .num').text(config.subscription_price);
						}
						$('.pay-subscription .cycle-unit').text('/first ' + config.cycle_unit);
					} else {
						$('.pay-subscription').addClass('hide');
					}

					$('#checkout-button').data('data', rdata);
				});
			},
			// 渲染paypal
			renderPaypal: function () {
				var layerThat = this;
				
				var removeLoad = layerThat.addLoading('.libPay-qcode-item:not(.hide)');
				var config = $('#libPay-theme-price .pay-pro-cycle .active').data();
				var param = { pid: config.pid, cycle: config.cycle, cycle_unit: config.cycle_unit, charge_type: config.charge_type };
				param.source = parseInt(bt.get_cookie('pay_source') || 0);
				if (param.source === 0) {
					if ($('.btpro-gray').length == 1) {
						// 是否免费版
						param.source = 27;
					} else {
						param.source = 28;
					}
				}
				if (!param.pid) delete param.pid;
				if (bt.get_cookie('serial_no') != null) param.serial_no = config.serial_no || bt.get_cookie('serial_no');
				that.pro.create_order(param, function (rdata) {
					removeLoad();

					if (rdata.status === false) {
						bt.set_cookie('force', 1);
						if (soft) soft.flush_cache();
						layer.msg(rdata.msg, { icon: 2 });
						return;
					}

					var cycle = config.cycle + ' ' + config.cycle_unit + (config.cycle > 1 ? 's' : '');
					// var unit = config.num + ' unit' + (config.num > 1 ? 's' : '');
					$('.libPayTotal').html('<span style="font-size: 18px; margin-left: 4px; margin-right: 2px">$</span>' + config.price);
					$('.pay-price .org_price').text('$' + config.market_price + '/' + cycle);
					$('.pay-price .libPayCycle').html('/' + cycle);

					layerThat.renderPaypalBtn(rdata);
				});
			},
			renderPaypalBtn: function (rdata) {
				$('#paypal-button-container').empty();

				jQuery.ajax({ 
					url: "/static/js/polyfill.min.js",
					dataType: "script",
					cache: true
				}).done(function() {
					var httpPromise = function (config) {
						return new Promise((resolve, reject) => {
							$.ajax({
								type: 'POST',
								url: config.url,
								data: config.data,
								success: function (res) {
									resolve(res)
								},
								error: function (err) {
									reject(err)
								}
							});
						})
					}
					var check_response = function (response) {
						return new Promise((resolve, reject) => {
							if (response.status) {
								return resolve(response.res);
							}
							bt.msg(response);
							reject(response.res);
						});
					}
					jQuery.ajax({ 
						url: "https://www.paypal.com/sdk/js?client-id=" + rdata.paypal_client_id,
						dataType: "script",
						cache: true
					}).done(function() {
						var buttons = paypal.Buttons({
							// 只渲染paypal支付按钮
							fundingSource: paypal.FUNDING.PAYPAL,
							// 绑定PayPal订单创建事件处理函数，请求paypal订单创建接口
							// 注意： 该函数必须返回Promise对象, 若使用 JQuery.ajax() 函数
							// 请使用 new Promise(fn(resolve(), reject())) 创建Promise对象并将其返回
							// Promise必须返回从接口获取的id
							createOrder: () => {
								return httpPromise({ 
									url: '/auth?action=get_paypal_session_id',
									data: { oid: rdata.order_id } 
								})
								.then(check_response)
								.then(res => res)
							},
							// 绑定支付确认事件，请求paypal订单支付确认接口并传递orderId
							// 注意： 该函数必须返回Promise对象，若使用 JQuery.ajax() 函数 请参照 step3
							// Promise最终请展示支付结果
							onApprove: (data) => {
								return httpPromise({
										url: '/auth?action=check_paypal_status',
										data: { paypal_order_id: data.orderID }
									})
									// res是支付成功跳转的url
									.then(check_response)
									.then(res => {
										layer.msg('Payment successful', { icon: 1 });
										setTimeout(() => {
											location.reload();
										}, 1500);
									})
							}
						})
						buttons.render('#paypal-button-container');
					});
				});
			},
			// 渲染抵扣卷
			renderVoucher: function (callback) {
				var layerThat = this;
				var config = layerThat.getConfig();
				var removeLoad = layerThat.addLoading('.libPay-qcode-item:not(.hide)');
				bt.soft.pro.get_voucher(config.pid, function (rdata) {
					removeLoad();

					if (callback) callback(rdata);

					$('.voucher-group').empty();
					if (rdata == null && !Array.isArray(rdata)) rdata = [];
					if (rdata.length == 0) {
						$('.voucher-group').addClass('hide');
						$('#use-voucher').addClass('disabled').text('No vouchers');
						return;
					}

					var $li = null
					that.each(rdata, function (index, item) {
						var name = (item.cycle_unit == 'month' && item.cycle == 999 ? '永久' : item.cycle + that.pro.conver_unit(item.cycle_unit));
						$li = $('<li class="pay-cycle-btn ' + (index === 0 ? 'active' : '') + '"><span>' + name + '</span></li>').data($.extend({ pid: config.pid }, item));
						$('.voucher-group').append($li);
					});

					$('.voucher-group').removeClass('hide');
					$('#use-voucher').removeClass('disabled').text('Pay');
					
				})
			},
			// 渲染授权列表
			renderAuthList: function (callback) {
				var layerThat = this;
				var config = layerThat.getConfig();
				var removeLoad = layerThat.addLoading('.libPay-qcode-item:not(.hide)');
				bt.send('get_product_auth', 'auth/get_product_auth', { page: 1, pageSize: 15, pid: config.pid }, function (rdata) {
					removeLoad();

					if (callback) callback(rdata);

					$('.auth-group').empty();
					if (rdata == null && !Array.isArray(rdata)) rdata = [];
					if (rdata.length == 0) {
						$('.auth-group').addClass('hide');
						$('#use-auth').addClass('disabled').text('No authorization');
						return;
					}

					var html = '';
					$.each(rdata, function (index, item) {
						if (config.pid == item.product_id) {
							html += '<li class="pay-cycle-btn  ' + (index == 0 ? 'active' : '') + '" data-id="' + item.serial_no + '" style="width:180px"><span>' + bt.format_data(item.end_time) + '</span></li>';
						}
					});
					$('.auth-group').append(html);
					$('.auth-group').removeClass('hide');
					$('#use-auth').removeClass('disabled').text('Authorization');
				})
			},
		});
	},
    product_cache:{}, //产品周期缓存
    order_cache:{},
    // 获取产品周期 ，并进行对象缓存
    get_product_discount_cache:function(config,callback){
      var that = this;
      if(typeof this.product_cache[config.pid] != "undefined"){
          if(callback) callback(this.product_cache[config.pid]);
      }else{
        bt.soft.pro.get_product_discount_by(config.pid,function(rdata){
          //rdata = {"36": {"discount": 1, "did": 0, "price": 3564, "name": "正常", "sprice": 3564}, "24": {"discount": 1, "did": 0, "price": 2376, "name": "正常", "sprice": 2376}, "12": {"discount": 1, "did": 0, "price": 1188, "name": "正常", "sprice": 1188}, "6": {"discount": 1, "did": 0, "price": 594, "name": "正常", "sprice": 594}, "3": {"discount": 1, "did": 0, "price": 297, "name": "正常", "sprice": 297}, "1": {"discount": 1, "did": 0, "price": 99, "name": "正常", "sprice": 99}, "pid": "100000045"};
          if(typeof rdata.status === "boolean"){
              if(!rdata.status) return false;
          }
          that.product_cache[config.pid] = rdata;
          setTimeout(function(){ delete that.product_cache[config.pid] },60000);
          if(callback) callback(rdata);
        });
      }
    },
    // 产品页面刷新
    product_pay_page_refresh: function (config) {
      var that = this;
      var condition = config.condition;
      switch (condition) {
        case 1:
          var loadT = bt.load();
          bt.send('get_product_auth', 'auth/get_product_auth', {page: 1, pageSize: 15,pid:config.pid}, function (res) {
            bt.soft.pro.get_voucher(config.pid, function (rdata) {
              loadT.close();
              var _arry = [
                {title: '微信支付', condition: 2},
                {title: 'Stripe', condition: 3},
                {title: 'voucher', condition: 4},
                {title: "Authorization", condition: 7, "_pid": config.pid}
              ];
              // if (config.renew) {
              //   _arry.splice(_arry.length - 1, 1);
              //   _arry[rdata.length > 0 ? '2' : '1'].active = true;
              //   config.condition = rdata.length > 0 ? 4 : 2;
              // } else {
                _arry[res.length > 0 ? '3' : (rdata.length > 0 ? '2' : '1')].active = true;
                config.condition = (res.length > 0 ? 7 : (rdata.length > 0 ? 4 : 3))
              // }
              if (res == null) res = [];
              if (rdata == null) rdata = [];
              $('#libPay-mode .li-con').empty().append(
                that.product_pay_swicth('payment', {
                  name: config.name,
                  pid: config.pid,
                  data: _arry,
                        voucher_data: rdata
                      })
                    );
              if (config.renew) {
                if (rdata.length > 0) config.voucher_data = rdata;
              } else {
                if (rdata.length > 0) config.voucher_data = rdata;
                if (res.length > 0) config.voucher_data = res;
              }
                    that.product_pay_page_refresh(config);
                  });
                });
              break;
        case 2:
        case 3:
          $('#libPay-content .li-tit').text('Choose your plan');
          config.pay = condition;
          if (config.pid == '100000030') {
            $('#libPay-tips').show();
          } else {
            $('#libPay-tips').hide();
          }
          var loadT = bt.load();
          bt.soft.get_product_discount_cache(config, function (rdata) {
            loadT.close();
            var _arry = [];
            var index = 0;
            try {
              delete rdata.pid
            } catch (error) {
              console.log(rdata.pid);
            }
            that.each(rdata, function (key, item) {
              _arry.push($.extend({cycle: parseInt(key)}, item));
            });
            _arry[index].active = true;
            $('#libPay-content .li-con').empty().append(
              that.product_pay_swicth('time', {
                name: config.name, pid: config.pid, data: _arry
              })
            );
            config.condition = 5;
            config = $.extend(config, _arry[index]);
            that.product_pay_page_refresh(config);
          });
          break;
        case 4:
          var loadP = bt.load("Getting deduction volume information!")
          clearInterval(bt.soft.pub.wxpayTimeId);
          $('#libPay-content').empty().append('<div class="li-tit c4"></div><div class="li-con c5"></div>');
          $('#libPay-pay').empty();
          $('#libPay-content .li-tit').text('Vouchers');
          $('#libPay-pay').removeAttr('data-qecode');
          $('#libPay-tips').hide();

        function callback(rdata) {
          loadP.close();
          if (rdata == null && !Array.isArray(rdata)) rdata = [];
          if (rdata.length == 0) {
            $('#libPay-content .li-con').empty()
            that.product_pay_page_refresh({condition: 6, pid: '', code: false});
            return false;
          }
                    rdata[0].active = true;
          $('#libPay-content .li-con').append(
            that.product_pay_swicth('voucher', {
              name: config.name,
              pid: config.pid,
              data: rdata
            })
          );
                    config.condition = 6;
                    that.product_pay_page_refresh($.extend(config, rdata[0]));
                }
                if (config.voucher_data) {
                    callback(config.voucher_data);
                } else {
                    bt.soft.pro.get_voucher(config.pid, function (rdata) {
                      callback(rdata);
                    });
                }
                break;
            case 5:
                $('#libPay-content .li-con').css('height', 'auto');
                $('.libPay-mask').show();
                if($('#libPay-pay').attr('data-qecode')) {
                var qcode = $('#libPay-content li').eq(config.dom_index).data('qrcode-url');
                $('#libPay-pay').find('.sale-price').html((config.price).toFixed(2));
                $('#libPay-pay').find('.cost-price').css('display', (config.sprice > config.price ? 'inline-block' : 'none')).html('$ '+(config.sprice).toFixed(2));
                $('#libPay-pay').find('#PayQcode').html('<div class="loading">Loading, please wait!</div>');
                if (qcode) {
                    $('#libPay-pay').find('#PayQcode').empty().qrcode(qcode);
                    that.product_pay_monitor({ pid: config.pid, name: config.name });
                    $('.libPay-mask').hide();
                    return false;
                  }
                }else{
                    $('#libPay-pay').html('<div class="cloading">Loading, please wait!</div>');
                }
                var paream = {pid:config.pid,cycle:config.cycle};
                paream.source = parseInt(bt.get_cookie('pay_source') || 0)
								console.log(paream.source)
                if (paream.source === 0) {
                    if ($('.btpro-gray').length == 1) {  // 是否免费版
                        paream.source = 27;
                    } else {
                        paream.source = 28;
                    }
                }
                if(!paream.pid) delete paream.pid;
                if(bt.get_cookie('serial_no') != null) paream.serial_no = config.serial_no  || bt.get_cookie('serial_no')
                that.pro.create_order(paream,function (rdata){
                  if (rdata.status === false){
                    bt.set_cookie('force', 1);
                    if (soft) soft.flush_cache();
                    layer.msg(rdata.msg, { icon: 2 });
                    return;
                  }
                  config.pay = parseInt($('#libPay-mode .pay-cycle-btn.active').data('condition'));
                  // 二维码显示界面
                  $('#libPay-pay').empty().append(that.product_pay_swicth((config.pay == 2?'wechat':'alipay'),$.extend({ order_no:rdata.order_no,stripe_publishable_key:rdata.stripe_publishable_key}, config)));
                });
                $("#libPay-pay").on('click','#checkout-button',function(){
                  var loadT = bt.load("Getting the session ID,Please waiting!")
                  var stripe = Stripe($(this).data('keys'));
                  that.pro.get_check_out_info($(this).data('code'),function(res){
                    loadT.close()
                    if (res.id) {
                      stripe.redirectToCheckout({sessionId: res.id});
                    } else {
                      layer.msg("Payment order failed, please contact administrator!", {icon: 2});
                    }
                  })
                })
              break;
        case 6:
          var _html = $('<div class="paymethod-submit text-center"></div>');
          var _button = $('<button class="btn btn-success btn-sm f16 ' + (config.serial_no ? '' : 'disabled') + '" style="width: 200px; height: 40px;">' + (config.serial_no ? 'Pay' : 'No vouchers') + '</button>');
          _button.click(function (ev) {
            if (!config.serial_no) {
              layer.msg('No vouchers');
              return false;
            }
            bt.soft.pro.create_order_voucher(config.pid, config.code, config.id, config.cycle, config.cycle_unit, config.charge_type, function (rdata) {
              layer.closeAll();
              bt.set_cookie('force', 1);
              if (soft) soft.flush_cache();
              bt.msg(rdata.res);
            });
          });
          $('#libPay-pay').empty().append(_html.append(_button));
          break;
        case 7:
          if (config.renew) return false
          var loadA = bt.load("Obtaining authorization information!")
          $('#libPay-content').empty().append('<div class="li-tit c4"></div><div class="li-con c5"></div>');
          $('#libPay-pay').empty();
          var _pid = config.pid;
          $('#libPay-content .li-tit').text('Authorization information');
          bt.send('get_product_auth', 'auth/get_product_auth', {page: 1, pageSize: 15,pid:config.pid}, function (res) {
            loadA.close();
            if (res.status == false) {
              layer.msg(res.msg, {icon: res.status ? 1 : 2});
              return false;
            }
            _html = $('<ul class="pay-btn-group"></ul>');
            if (res.length == 0) {
              _html.append($('<li class="pay-cycle-btn" id="no_authorization" style="width:180px;cursor: default;" disabled="disabled"><span> No authorization</span></li>'));
            }
                    var  authorization_flag = false;
                    $.each(res, function (index, item) {
                        if(_pid == item.product_id){
                            _html.append($('<li class="pay-cycle-btn  ' + (index==0 ? 'active' : '') + '" data-id="' + item.serial_no + '" style="width:180px"><span>' + bt.format_data(item.end_time) + '</span></li>'));
                            authorization_flag = true;
                        }
                        if(authorization_flag == false && index == res.length - 1){
                            _html.append($('<li class="pay-cycle-btn" id="no_authorization" style="width:180px;cursor: default;" disabled="disabled"><span> No authorization</span></li>'));
                        }
                    });
                        $('#libPay-content .li-con').empty().append(_html);
                        $('#libPay-content ul li').click(function () {
                            $(this).addClass('active').siblings().removeClass('active')
                        });
                        $('#libPay-pay').empty().append($('<div class="lib-price-box text-center"><button type="button" id="authorization" style="margin-top:30px" class="btn btn-success ">Authorization</button></div>'));
                        //授权
                        $('#authorization').unbind();
                        var html = $('#libPay-content .li-con ul li  span').html() || '';
                        if (html.indexOf("No authorization") > 0) {
                            $('#authorization').attr("disabled", "disabled");
                        } else {
                            $('#authorization').removeAttr("disabled");
                            $('#authorization').on('click', function (e) {
                                var _serial_no = $('#libPay-content .active').attr('data-id');
                                if (typeof _serial_no == 'undefined') return false;
                                var loadU = bt.load("Under licensing!");
                                bt.send('auth_activate', 'auth/auth_activate', {serial_no: _serial_no}, function (res) {
                                    loadU.close()
                                    if (res) {
                                        layer.msg(res.msg, {icon: res.status ? 1 : 2});
                                        if (res.status) {
                                            window.location.reload();
                                        }
                                    }
                                });
                            })
                    }
                });
                break;

        }
    },
    // 产品购买，渲染方法
    product_pay_swicth: function (type,config){
        var _html = '', that = this;
        switch (type) {
            case 'type': // 产品类型（配置参数）
                _html = $('<ul class="li-c-item"></ul>');
                this.each(config, function (index, item) {
                    _html.append($('<li class="pay-cycle-btn ' + (item.active ? 'active' : '') + '">' +
                        (item.recommend ? '<span class="recommend-pay-icon"></span>' : '') +
                        '<span class="item-name pull-left">' + item.title + '</span>' +
                        '<span class="item-info f12 pull-right c7">' + item.ps + '</span>' +
                        '</li>').data(item).click(function(ev){
                            var data = $(this).data();
                            if (!$(this).hasClass('active')) that.product_pay_page_refresh($.extend({ condition: 1 }, data));
                            $(this).addClass('active').siblings().removeClass('active');

                        }));
                });
                break;
           case 'payment':// 产品付款方式
                _html = $('<ul class="pay-btn-group"></ul>');
                this.each(config.data, function (index, item) {
                    if(item.title !="微信支付"){
                        _html.append($('<li class="pay-cycle-btn ' + (item.active ? 'active' : '') + '" data-condition="' + item.condition + '"><span>' + item.title + '</span></li>').data($.extend({ pid: config.pid, name: config.name }, item)).click(function (ev) {
                            var data = $(this).data();
                            if (!$(this).hasClass('active')) that.product_pay_page_refresh($.extend({ condition: $(this).attr('data-condition') }, data));
                            $(this).addClass('active').siblings().removeClass('active');
                        }));
                    }
                });
                break;
            case 'time': // 产品开通时长（配置参数）
              _html = $('<ul class="pay-btn-group"></ul>');
              this.each(config.data, function (index, item) {
                _html.append($('<li class="pay-cycle-btn ' + (item.active ? 'active' : '') + '"><span data-unit=' + item.cycle_unit + '>' + that.pro.conver_unit(item.cycle + item.cycle_unit) + '</span>' + (item.discount_rate != 1 ? '<em style="width:50px">' + (100 - item.discount_rate * 100) + '% off</em>' : '') + '</li>').data($.extend({
                  pid: config.pid,
                  dom_index: index
                }, item)).click(function (ev) {
                  var data = $(this).data();
                  if (!$(this).hasClass('active')) that.product_pay_page_refresh($.extend({condition: 5}, data));
                  $(this).addClass('active').siblings().removeClass('active');
                }));
              });
              break;
          case 'voucher':// 产品抵扣卷（配置参数）
            _html = $('<ul class="pay-btn-group voucher-group"></ul>');

            this.each(config.data, function (index, item) {
              _html.append($('<li class="pay-cycle-btn ' + (item.active ? 'active' : '') + '"><span>' + (item.cycle_unit == 'month' && item.cycle == 999 ? '永久' : (item.cycle + that.pro.conver_unit(item.cycle_unit))) + '</span></li>').data($.extend({pid: config.pid}, item)).click(function (ev) {
                var data = $(this).data();
                $(this).addClass('active').siblings().removeClass('active');
                that.product_pay_page_refresh($.extend({condition: 6}, data));
              }));
            });
            break;
          case 'wechat':
            case 'alipay':
                _html = $('<div class="lib-price-box text-center">' +
                    '<span class="lib-price-name f14"><b>Total</b></span>' +
                    '<span class="price-txt"><b class="sale-price">$' + (config.price).toFixed(2) + '</b></span>' +
                    '<s class="cost-price" style="display: ' + (config.market_price > config.price ? 'inline-block' : 'none') + ';">$ ' + (config.market_price).toFixed(2) + '</s></div>' +
                    '<div class="lib-price-box text-center">' +
                    '<button type="button" id="checkout-button" style="margin-top:30px" class="btn btn-success " data-code="'+config.order_no+'" data-keys="'+config.stripe_publishable_key+'">Pay Now</button>'
                );
                // $(_html).find('#PayQcode').qrcode(config.data);
                $('.libPay-mask').hide();
                // that.product_pay_monitor({ pid: config.pid, name: config.name });
                break;
        }
        return _html;
    },

	// 支付状态监听
	product_pay_monitor:function(config){
		var that = this;
		function callback(rdata){
			if(rdata.status){
				clearInterval(bt.soft.pub.wxpayTimeId);
				layer.closeAll();
				var title = '';
				if(config.pid == 100000032 || config.pid === ''){
					title = config.pid === ''?'专业版支付成功！':'企业版支付成功！';
					setTimeout(function(){
						bt.set_cookie('force',1);
						if(soft) soft.flush_cache();
						location.reload(true);
					},2000);   // 需要重服务端重新获取软件列表，并刷新软件管理浏览器页面
				}else{
					title = config.name + '插件支付成功！';
					setTimeout(function(){
						bt.set_cookie('force',1);
						if(soft) soft.flush_cache();
						location.reload(true);
					},2000);   // 需要重服务端重新获取软件列表，
				}
				bt.msg({ msg:title, icon: 1,shade: [0.3, "#000"] });
			}
		}
		clearInterval(bt.soft.pub.wxpayTimeId);
		function intervalFun(){
			if(config.pid){
				that.pro.get_plugin_coupon(config.pid,callback);
			}else{
				that.pro.get_re_order_status(callback);
			}
		}
		intervalFun();
		bt.soft.pub.wxpayTimeId = setInterval(function () {
			intervalFun();
		},2500);
	},
	updata_ltd:function(is_alone){
		var param = {name:'宝塔面板企业版',pid:100000032,limit:'ltd'};
		if(is_alone || false) $.extend(param,{source:5,is_alone:true});
		bt.soft.product_pay_view(param);
	},
    //遍历数组和对象
	each:function(obj, fn){
		var key,that = this;
		if(typeof fn !== 'function') return that;
		obj = obj || [];
		if(obj.constructor === Object){
			for(key in obj){
			if(fn.call(obj[key], key, obj[key])) break;
			}
		} else {
			for(key = 0; key < obj.length; key++){
			if(fn.call(obj[key], key, obj[key])) break;
			}
		}
		return that;
    },
  /**
   * @description 升级专业版
   */
  updata_pro: function (num) {
      var param = {
          name: 'Pro',
          pid: 100000058,
          limit: 'pro'
      }
      if(num) param['totalNum'] = num;
      bt.set_cookie('pay_source', num);
      bt.soft.product_pay_view(param);
  },
  /**
   * @description 续费专业版
   */
  renew_pro: function () {
    var config = {name: 'Pro', pid: '100000058', limit: 'pro', renew: true};
    if (!bt.get_cookie('serial_no')) delete config.renew;
    bt.soft.product_pay_view(config);
  },
    // updata_pro: function() {
    //     bt.pub.get_user_info(function(rdata) {
    //         if (!rdata.status) {
    //             bt.pub.bind_btname(0, function(rdata) {
    //                 if (rdata.status) bt.soft.updata_pro();
    //             })
    //             return;
    //         }
    //         var payhtml = '<div class="libPay" style="padding:15px 30px 30px 30px">\
	// 				<div class="libpay-con">\
	// 				</div>\
	// 				<p style="position:absolute;bottom:17px;left:0;width:100%;text-align:center;color:red">' + lan.public_backup.buy_multiplev_bt_pro + '<a class="btlink" href="https://www.bt.cn/download/linuxpro.html#price" target="_blank">' + lan.public_backup.goto_bt + '</a></p>\
	// 			</div>';

    //         bt.open({
    //             type: 1,
    //             title: lan.public_backup.up_pro_use_allplug_free,
    //             area: ['616px', '540px'],
    //             closeBtn: 2,
    //             shadeClose: false,
    //             content: payhtml
    //         });
    //         setTimeout(function() {
    //             bt.soft.get_product_discount('', 0);
    //             $(".pay-btn-group > li").click(function() {
    //                 $(this).addClass("active").siblings().removeClass("active");
    //             });
    //         }, 100)
    //     })
    // },
    re_plugin_pay: function(pluginName, pid, type) {
        bt.pub.get_user_info(function(rdata) {
            if (!rdata.status) {
                bt.pub.bind_btname(0, function(rdata) {
                    if (rdata.status) bt.soft.re_plugin_pay(pluginName, pid, type);
                })
                return;
            }
            var txt = lan.public_backup.buy;
            if (type) txt = lan.public_backup.renew;
            var payhtml = '<div class="libPay" style="padding:15px 30px 30px 30px">\
					<div class="libPay-item f14 plr15 libPay-select">\
						<div class="li-tit c3">' + lan.public_backup.type + '</div>\
						<div class="li-con c6">\
							<ul class="li-c-item">\
								<li class="active"><span class="item-name pull-left">' + pluginName + '</span><span class="item-info f12 pull-right c7">' + lan.public_backup.apiece_of_plug + '</span></li>\
								<li><span class="item-name">' + lan.public_backup.up_pro + '</span><span class="item-info f12 pull-right c7">' + lan.public_backup.use_allplug_free + '</span></li>\
							</ul>\
						</div>\
					</div>\
					<div class="libpay-con">\
					</div>\
				</div>';

            layer.open({
                type: 1,
                title: txt + pluginName,
                area: ['616px', '680px'],
                closeBtn: 2,
                shadeClose: false,
                content: payhtml
            });
            setTimeout(function() {
                bt.soft.get_product_discount(pluginName, pid);
                $(".li-c-item li").click(function() {
                    var i = $(this).index();
                    $(this).addClass("active").siblings().removeClass("active");
                    if (i == 0) {
                        bt.soft.get_product_discount(pluginName, pid);
                        $(".pro-info").hide();
                    } else {
                        bt.soft.get_product_discount('', 0);
                        $(".pro-info").show();
                    }
                });
                $(".pay-btn-group > li").click(function() {
                    $(this).addClass("active").siblings().removeClass("active");
                });
            }, 100)
        })
    },

    re_plugin_pay_other: function(pluginName, pid, type, price) {
        bt.pub.get_user_info(function(rdata) {
            if (!rdata.status) {
                bt.pub.bind_btname(0, function(rdata) {

                })
                return;
            }
            var txt = lan.public_backup.buy;
            if (type) txt = lan.public_backup.renew;
            var payhtml = '<div class="libPay" style="padding:15px 30px 30px 30px">\
              <div class="libpay-con">\
                <div class="payment-con">\
                  <div class="pay-weixin">\
                    <div class="libPay-item f14 plr15">\
                      <div class="li-tit c4">' + txt + lan.public_backup.duration + '</div>\
                      <div class="li-con c6" id="PayCycle"><ul class="pay-btn-group">\
                          <li class="pay-cycle-btn active" onclick="bt.soft.get_rscode_other(' + pid + ',' + price + ',1,' + type + ')"><span>' + lan.public_backup.month1 + '</span></li>\
                          <li class="pay-cycle-btn" onclick="bt.soft.get_rscode_other(' + pid + ',' + price + ',3,' + type + ')"><span>' + lan.public_backup.month3 + '</span></li>\
                          <li class="pay-cycle-btn" onclick="bt.soft.get_rscode_other(' + pid + ',' + price + ',6,' + type + ')"><span>' + lan.public_backup.month6 + '</span></li>\
                          <li class="pay-cycle-btn" onclick="bt.soft.get_rscode_other(' + pid + ',' + price + ',12,' + type + ')"><span>' + lan.public_backup.year + '</span></li>\
                      </ul></div>\
                    </div>\
                    <div class="lib-price-box text-center"><span class="lib-price-name f14"><b>' + lan.public_backup.total + '</b></span><span class="price-txt"><b class="sale-price"></b>' + lan.public_backup.rmb + '</span><s class="cost-price"></s></div>\
                    <div class="paymethod">\
                      <div class="pay-wx"></div>\
                      <div class="pay-wx-info f16 text-center"><span class="wx-pay-ico mr5"></span>' + lan.public_backup.pay_by_wechatqrcore + '</div>\
                    </div>\
                  </div>\
                </div>\
              </div>\
            </div>';

            layer.open({
                type: 1,
                title: txt + pluginName,
                area: ['616px', '450px'],
                closeBtn: 2,
                shadeClose: false,
                content: payhtml
            });
            bt.soft.get_rscode_other(pid, price, 1, type)
            setTimeout(function() {
                $(".pay-btn-group > li").click(function() {
                    $(this).addClass("active").siblings().removeClass("active");
                });
            }, 100);
        })
    },
    get_rscode_other: function(pid, price, cycle, type) {
        var loadT = layer.msg(lan.public_backup.get_payment_info, { icon: 16, time: 0, shade: 0.3 });
        $.post('/auth?action=create_plugin_other_order', { pid: pid, cycle: cycle, type: type }, function(rdata) {
            layer.close(loadT);
            if (!rdata.status) {
                layer.closeAll();
                layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
                return;
            }

            if (!rdata.msg.code) {
                layer.closeAll();
                layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
                soft.flush_cache();
                return;
            }
            $(".sale-price").text((price * cycle).toFixed(2))
            $(".pay-wx").html('');
            $(".pay-wx").qrcode(rdata.msg.code);
            bt.set_cookie('other_oid', rdata.msg.oid)
            bt.soft.get_order_stat(rdata.msg.oid, type);
        });
    },
    get_order_stat: function(order_id, type) {
        if (bt.get_cookie('other_oid') != order_id) return;
        setTimeout(function() {
            $.post('/auth?action=get_order_stat', { oid: order_id, type: type }, function(stat) {
                if (stat == 1) {
                    layer.closeAll();
                    soft.flush_cache();
                    return;
                }

                if ($(".pay-btn-group").length > 0) {
                    bt.soft.get_order_stat(order_id, type);
                }
            });

        }, 1000)
    },
    get_voucher_list: function(pid) {
        $("#couponlist").html("<div class='cloading'>" + lan.public_backup.loading + "</div>");
        bt.soft.pro.get_voucher(pid, function(rdata) {
            if (rdata != null && rdata.length > 0) {
                var con = '';
                var len = rdata.length;
                for (var i = 0; i < len; i++) {
                    if (rdata[i].status != 1) {
                        var cyc = rdata[i].cycle + bt.soft.pro.conver_unit(rdata[i].unit);
                        if (rdata[i].cycle == 999) {
                            cyc = lan.public_backup.permanent
                        }
                        con += '<li class="pay-cycle-btn" data-coupon-id ="' + rdata[i].id + '" data-charge-type ="' + rdata[i].charge_type + '"  data-code="' + rdata[i].code + '"><span>' + cyc + '</span></li>';
                    }
                }
                $("#couponlist").html('<ul class="pay-btn-group">' + con + '</ul>');
                $(".pay-btn-group > li").click(function() {
                    $(this).addClass("active").siblings().removeClass("active");
                    $(".paymethod-submit button").css({ "background-color": "#20a53a", "border-color": "#20a53a" });
                });
                $(".paymethod-submit button").click(function() {
                    var _active = $("#couponlist .pay-btn-group .active"),
                    code = _active.attr("data-code"),
                    coupon_id = _active.attr("data-coupon-id"),
                    charge_type = _active.attr("data-charge-type");

                    var  _span = $("#couponlist .pay-btn-group .active span"),
                    cycle = parseInt(_span.html()),cycle_unit = _span.html.indexOf("Month")?"month":"year";
                    if (code == undefined) {
                        layer.msg(lan.public_backup.choose_cash_coupon);
                    } else {
                        bt.soft.pro.create_order_voucher(pid, code, coupon_id, cycle, cycle_unit, charge_type,function(rdata) {
                            layer.closeAll();
                            bt.set_cookie('force', 1);
                            if (soft) soft.flush_cache();
                            bt.msg(rdata.res);
                        });
                    }
                })
            } else {
                $("#couponlist").html("<p class='text-center' style='margin-top:70px'>" + lan.public_backup.no_cash_coupon + "</p>");
            }
        })
    },
    get_rscode: function(pid, price, sprice, cycle) {
        $(".sale-price").text(price);
        if (price == sprice) {
            $(".cost-price").text(sprice + lan.public_backup.rmb).hide();
        } else {
            $(".cost-price").text(sprice + lan.public_backup.rmb).show();
        }
        $(".pay-wx").html('<span class="loading">' + lan.public_backup.loading + '</span>');
        $(".libPay").append('<div class="payloadingmask" style="height:100%;width:100%;position:absolute;top:0;left:0;z-index:1"></div>');
        bt.soft.pro.create_order(pid, cycle, function(rdata) {
            $(".payloadingmask").remove();
            if (rdata.status === false) {
                bt.set_cookie('force', 1);
                if (soft) soft.flush_cache();
                layer.msg(rdata.msg, { icon: 2 });
                return;
            }
            $(".pay-wx").html('');
            $(".pay-wx").qrcode(rdata.msg);
            clearInterval(bt.soft.pub.wxpayTimeId);
            if (pid) {
                bt.soft.pub.wxpayTimeId = setInterval(function() {
                    bt.soft.pro.get_plugin_coupon(pid, function(rdata) {
                        if (rdata.status) {
                            layer.closeAll();
                            clearInterval(bt.soft.pub.wxpayTimeId);
                            bt.msg({ msg: lan.public_backup.pay_plug_success, icon: 16, time: 0, shade: [0.3, "#000"] });
                            bt.set_cookie('force', 1);
                            if (soft) soft.flush_cache();
                            return;
                        }
                    })
                }, 3000);
            } else {
                bt.soft.pub.wxpayTimeId = setInterval(function() {
                    bt.soft.pro.get_re_order_status(function(rdata) {
                        if (rdata.status) {
                            layer.closeAll();
                            clearInterval(bt.soft.pub.wxpayTimeId);
                            bt.msg({ msg: lan.public_backup.pay_pro_success, icon: 16, time: 0, shade: [0.3, "#000"] });
                            bt.set_cookie('force', 1);
                            if (soft) soft.flush_cache();
                            return;
                        }
                    })
                }, 3000);
            }


        });
    },
    get_product_discount: function(pluginName, pid) {
        if (pluginName == undefined) pluginName = '';
        if (pid == undefined) pid = 0;
        var con = '<div class="libPay-item f14 plr15">\
							<div class="li-tit c4">' + lan.public_backup.pay_method + '</div>\
							<div class="li-con c6" id="Payment"><ul class="pay-btn-group pay-cycle"><li class="pay-cycle-btn active"><span>' + lan.public_backup.pay_by_wechat + '</span></li><li class="pay-cycle-btn" onclick="bt.soft.get_voucher_list(' + pid + ')"><span>' + lan.public_backup.cash_coupon + '</span></li></ul></div>\
						</div>\
						<div class="payment-con">\
							<div class="pay-weixin">\
								<div class="libPay-item f14 plr15">\
									<div class="li-tit c4">' + lan.public_backup.opening_time + '</div>\
									<div class="li-con c6" id="PayCycle"></div>\
								</div>\
								<div class="lib-price-box text-center"><span class="lib-price-name f14"><b>' + lan.public_backup.total + '</b></span><span class="price-txt"><b class="sale-price"></b>' + lan.public_backup.rmb + '</span><s class="cost-price"></s></div>\
								<div class="paymethod">\
									<div class="pay-wx"></div>\
									<div class="pay-wx-info f16 text-center"><span class="wx-pay-ico mr5"></span>' + lan.public_backup.pay_by_wechatqrcore + '</div>\
								</div>\
							</div>\
							<div class="pay-coupon" style="display:none">\
								<div class="libPay-item f14 plr15">\
									<div class="li-tit c4 ">' + lan.public_backup.cash_coupon_list + '</div>\
									<div class="li-con c6" id="couponlist"><div class="btn-group"></div></div>\
								</div>\
								<div class="paymethod-submit text-center">\
									<button class="btn btn-success btn-sm f16" style="width:200px;height:40px;background-color:#999;border-color:#888">' + lan.public_backup.submit + '</button>\
								</div>\
							</div>\
						</div>'
        $(".libpay-con").html("<div class='cloading'>" + lan.public_backup.loading + "</div>");

        bt.soft.pro.get_product_discount_by(pluginName, function(rdata) {
            if (rdata != null) {
                var coucon = '';
                var qarr = Object.keys(rdata);
                var qlen = qarr.length;
                if (pluginName) qlen = qlen - 1;
                //折扣列表
                for (var i = 0; i < qlen; i++) {
                    var j = qarr[i];
                    var a = rdata[j].price.toFixed(2);
                    var b = rdata[j].sprice.toFixed(2);
                    var c = rdata[j].discount;
                    coucon += '<li class="pay-cycle-btn" onclick="bt.soft.get_rscode(' + pid + ',' + a + ',' + b + ',' + j + ')"><span>' + bt.soft.pro.conver_unit(j) + '</span>' + (c == 1 ? "" : '<em>' + c * 10 + lan.public_backup.discount + '</em>') + '</li>';
                }
                $(".libpay-con").html(con);
                $("#PayCycle").html('<ul class="pay-btn-group">' + coucon + '</ul>');
                $(".pay-btn-group li").click(function() {
                    $(this).addClass("active").siblings().removeClass("active");
                });
                $(".pay-cycle li").click(function() {
                    var i = $(this).index();
                    $(this).addClass("active").siblings().removeClass("active");
                    $(".payment-con > div").eq(i).show().siblings().hide();
                });
                $("#PayCycle .pay-btn-group li").eq(0).click();
            }
        })
    },
    get_index_list: function(callback) {
        bt.send('get_index_list', 'plugin/get_index_list', {}, function(rdata) {
            if (callback) callback(rdata);
        })
    },
    set_sort_index: function(data, callback) {
        var loading = bt.load();
        bt.send('sort_index', 'plugin/sort_index', { ssort: data }, function(rdata) {
            loading.close();
            if (callback) callback(rdata);
        })
    },
    get_soft_list: function(p, type, search, callback) {
        if (p == undefined) p = 1;
        if (type == undefined) type = 0;
        if (search == undefined) search = '';
        var force = bt.get_cookie('force');
        if (force == undefined) force = 0;
        p = p + ''
        if (p.indexOf('not_load') == -1) {
            var loading = bt.load(lan.public.the, 1);
        } else {
            var loading = null;
            p = p.split("not_load")[0];
        }

        bt.send('get_soft_list', 'plugin/get_soft_list', { p: p, type: type, tojs: 'soft.get_list', force: force, query: search }, function(rdata) {
          if (loading) loading.close();
          bt.set_cookie('force', 0);
          if(rdata.pro_authorization_sn != null){
            bt.set_cookie('serial_no',rdata.pro_authorization_sn);
          }else{
            bt.clear_cookie('serial_no')
          }
          bt.set_cookie('pro_end',rdata.pro);
          if (callback) callback(rdata);
        })
    },
    to_index: function(name, callback) {
        var status = $("#index_" + name).prop("checked") ? "0" : "1";
        if (name.indexOf('php-') >= 0) {
            var verinfo = name.replace(/\./, "");
            status = $("#index_" + verinfo).prop("checked") ? "0" : "1";
        }
        if (status == 1) {
            bt.send('add_index', 'plugin/add_index', { sName: name }, function(rdata) {
                rdata.time = 1000;
                if (!rdata.status) bt.msg(rdata);
                if (callback) callback(rdata);
            })
        } else {
            bt.send('remove_index', 'plugin/remove_index', { sName: name }, function(rdata) {
                rdata.time = 1000;
                if (!rdata.status) bt.msg(rdata);
                if (callback) callback(rdata);
            })
        }
    },
    add_make_args: function (name, init) {
        name = bt.soft.get_name(name);
        pdata = {
            name: name,
            args_name: $("input[name='make_name']").val(),
            init: init,
            ps: $("input[name='make_ps']").val(),
            args: $("input[name='make_args']").val()
        }
        if (pdata.args_name.length < 1 || pdata.args.length < 1) {
            layer.msg('Custom module name and parameter cannot be empty!');
            return
        }
        loadT = bt.load('Adding custom module...')
        bt.send('add_make_args', 'plugin/add_make_args', pdata, function (rdata) {
            loadT.close();
            bt.soft.get_make_args(name);
            bt.msg(rdata);
            if (rdata.status === true) bt.soft.loadOpen.close();
        })
    },
    show_make_args: function (name) {
        name = bt.soft.get_name(name);
        var _aceEditor = '';
        bt.soft.loadOpen = bt.open({
            type: 1,
            title: 'Add custom module',
            area: '500px',
            btn: [lan.public.submit, lan.public.close],
            content: '<div class="bt-form c6">\
				<from class="bt-form" id="outer_url_form" style="padding:30px 10px;display:inline-block;">\
					<div class="line">\
						<span class="tname">Name</span>\
						<div class="info-r" style="margin-left: 100px;">\
							<input name="make_name" class="bt-input-text mr5" type="text" placeholder="Enter module name e.g., test_1" style="width:350px" value="">\
						</div>\
					</div>\
					<div class="line">\
						<span class="tname">Details</span>\
						<div class="info-r" style="margin-left: 100px;">\
							<input name="make_ps" class="bt-input-text mr5" placeholder="Description within 30 words" type="text" style="width:350px" value="">\
						</div>\
					</div>\
					<div class="line">\
						<span class="tname">Parameter</span>\
						<div class="info-r" style="margin-left: 100px;">\
							<input name="make_args" class="bt-input-text mr5" type="text" placeholder="As：--add-module=/tmp/echo/echo-nginx-module-master" style="width:350px" value="">\
						</div>\
					</div>\
					<div class="line">\
						<span class="tname">Prefix script</span>\
						<div class="info-r" style="margin-left: 100px;">\
							<div id="preposition_shell" class="bt-input-text" style="height:300px;width:350px;font-size:11px;line-height:20px;"></div>\
						</div>\
					</div>\
				</from>\
			</div>',
            success: function (layer, index) {
                _aceEditor = ace.edit('preposition_shell', {
                    theme: "ace/theme/chrome", //主题
                    mode: "ace/mode/sh", // 语言类型
                    wrap: true,
                    showInvisibles: false,
                    showPrintMargin: false,
                    showFoldWidgets: false,
                    useSoftTabs: true,
                    tabSize: 2,
                    showPrintMargin: false,
                    readOnly: false
                });
                _aceEditor.setValue('# The shell script content executed before compilation is usually prepared for the dependent installation and source download of the third-party module');
            },
            yes: function () {
                bt.soft.add_make_args(name, _aceEditor.getValue());
            }
        })
    },
    modify_make_args: function (name, args_name) {
        name = bt.soft.get_name(name);
        var _aceEditor = '';
        bt.soft.loadOpen = bt.open({
            type: 1,
            title: 'Edit custom option module[' + name + ':' + args_name + ']',
            area: '500px',
            btn: [lan.public.submit, lan.public.close],
            content: '<div class="bt-form c6">\
				<from class="bt-form" id="outer_url_form" style="padding:30px 10px;display:inline-block;">\
					<div class="line">\
						<span class="tname" style="width: 125px;padding-right: 5px;">Module name</span>\
						<div class="info-r">\
							<input name="make_name" class="bt-input-text mr5" type="text" placeholder="Only letters, numbers, underscores" style="width:350px" value="'+ bt.soft.make_data[args_name].name + '">\
						</div>\
					</div>\
					<div class="line">\
						<span class="tname" style="width: 125px;padding-right: 5px;">Module details</span>\
						<div class="info-r">\
							<input name="make_ps" class="bt-input-text mr5" placeholder="Description within 30 words" type="text" style="width:350px" value="'+ bt.soft.make_data[args_name].ps + '">\
						</div>\
					</div>\
					<div class="line">\
						<span class="tname" style="width: 125px;padding-right: 5px;">Module parameter</span>\
						<div class="info-r">\
							<input name="make_args" class="bt-input-text mr5" type="text" placeholder="As：--add-module=/tmp/echo/echo-nginx-module-master" style="width:350px" value="'+ bt.soft.make_data[args_name].args + '">\
						</div>\
					</div>\
					<div class="line">\
						<span class="tname" style="width: 125px;padding-right: 5px;">Prefix script</span>\
						<div class="info-r">\
							<div id="preposition_shell" class="bt-input-text" style="height:300px;width:350px;font-size:11px;line-height:20px;"></div>\
						</div>\
					</div>\
				</from>\
			</div>',
            success: function (layer, index) {
                _aceEditor = ace.edit('preposition_shell', {
                    theme: "ace/theme/chrome", //主题
                    mode: "ace/mode/sh", // 语言类型
                    wrap: true,
                    showInvisibles: false,
                    showPrintMargin: false,
                    showFoldWidgets: false,
                    useSoftTabs: true,
                    tabSize: 2,
                    showPrintMargin: false,
                    readOnly: false
                });
                _aceEditor.setValue(bt.soft.make_data[args_name].init);
            },
            yes: function () {
                bt.soft.add_make_args(name, _aceEditor.getValue());
            }
        })
    },
    set_make_args: function (_this, name, args_name) {
        name = bt.soft.get_name(name);
        if ($('.args_' + args_name)[0].checked) {
            bt.soft.make_config.push(args_name)
        } else {
            index = bt.soft.make_config.indexOf(args_name)
            if (index === -1) return;
            bt.soft.make_config.splice(index, 1);
        }
        index = bt.soft.make_config.indexOf('')
        if (index !== -1) bt.soft.make_config.splice(index, 1);
        bt.send('set_make_args', 'plugin/set_make_args', { name: name, args_names: bt.soft.make_config.join("\n") }, function (rdata) {
            if (!rdata.status) {
                bt.msg(rdata)
            }
        })
    },
    //遍历数组和对象
	each:function(obj, fn){
		var key,that = this;
		if(typeof fn !== 'function') return that;
		obj = obj || [];
		if(obj.constructor === Object){
			for(key in obj){
			if(fn.call(obj[key], key, obj[key])) break;
			}
		} else {
			for(key = 0; key < obj.length; key++){
			if(fn.call(obj[key], key, obj[key])) break;
			}
		}
		return that;
	},
    del_make_args: function (name, args_name) {
        name = bt.soft.get_name(name);
        bt.confirm({ msg: 'Confirm delete[' + name + ':' + args_name + ']module？', title: 'Delete[' + name + ':' + args_name + ']module!' }, function () {
            loadT = bt.load('Removing module[' + args_name + ']...')
            bt.send('del_make_args', 'plugin/del_make_args', { name: name, args_name: args_name }, function (rdata) {
                bt.soft.get_make_args(name);
                bt.msg(rdata);
            });
        });
    },
    get_make_args: function (name) {
        name = bt.soft.get_name(name);
        loadT = bt.load('Getting optional modules...')
        bt.send('get_make_args', 'plugin/get_make_args', { name: name }, function (rdata) {
            loadT.close();
            var module_html = '';
            bt.soft.make_config = rdata.config.split("\n")
            bt.soft.make_data = {}
            for (var i = 0; i < rdata.args.length; i++) {
                bt.soft.make_data[rdata.args[i].name] = rdata.args[i]
                var checked_str = (bt.soft.make_config.indexOf(rdata.args[i].name) == -1 ? '' : 'checked="checked"')
                module_html += '<tr>\
									<td>\
										<input class="args_'+ rdata.args[i].name + '" onclick="bt.soft.set_make_args(this,\'' + name + '\',\'' + rdata.args[i].name + '\')" type="checkbox" ' + checked_str + ' />\
									</td>\
									<td>'+ rdata.args[i].name + '</td><td>' + rdata.args[i].ps + '</td>\
									<td>\
										<a onclick="bt.soft.modify_make_args(\''+ name + '\',\'' + rdata.args[i].name + '\')" class="btlink">Edit</a>\
										| <a onclick="bt.soft.del_make_args(\''+ name + '\',\'' + rdata.args[i].name + '\')" class="btlink">Del</a>\
									</td>\
								</tr>';
            }
            $(".modules_list").html(module_html);
        });
    },
    check_make_is: function (name) {
        name = bt.soft.get_name(name);
        var shows = ["nginx", 'apache', 'mysql', 'php']
        for (var i = 0; i < shows.length; i++) {
            if (name.indexOf(shows[i]) === 0) {
                return true
            }
        }
        return false
    },
    get_name: function (name) {
        if (name.indexOf('php-') === 0) {
            return 'php';
        }
        return name
    },
    install: function (name, that) {
        var _this = this;
        if (bt.soft.is_install) {
            layer.msg('Installing other software, please operate later!', {icon: 0});
            return false;
        }
        _this.get_soft_find(name, function (rdata) {
            var arrs = ['apache', 'nginx', 'mysql'];
            if ($.inArray(name, arrs) >= 0 || name.indexOf('php-') >= 0) {
                var SelectVersion = '', shtml = name;
                if (rdata.versions.length > 1) {
                    for (var i = 0; i < rdata.versions.length; i++) {
                        var item = rdata.versions[i];
                        SelectVersion += '<option>' + name + ' ' + item.m_version + '</option>';
                    }
                    shtml = "<select id='SelectVersion' class='bt-input-text' style='margin-left:30px'>" + SelectVersion + "</select>";
                } else {
                    shtml = "<span id='SelectVersion'>" + name + "</span>";
                }
                var loadOpen = bt.open({
                    type: 1,
                    title: name + lan.soft.install_title,
                    area: '400px',
                    content: "<div class='bt-form pd20 pd20 c6' style='padding-bottom:50px'>\
						<div class='version line' style='padding-left:15px'>" + lan.soft.install_version + "：" + shtml + "</div>\
                        <div class='fangshi line' style='padding-left:15px'>" + lan.bt.install_type + "：<label data-title='" + lan.bt.install_src_title + "'>" + lan.bt.install_src + "<input type='checkbox'></label><label data-title='" + lan.bt.install_rpm_title + "'>" + lan.bt.install_rpm + "<input type='checkbox' checked></label></div>\
                        <div class='install_modules' style='display: none;'>\
							<div style='margin-bottom:15px;padding-top:15px;border-top:1px solid #ececec;'><button onclick=\"bt.soft.show_make_args(\'" + name + "\')\" class='btn btn-success btn-sm'>Add custom module</button></div>\
							<div class='select_modules divtable' style='margin-bottom:20px'>\
								<table class='table table-hover'>\
									<thead>\
										<tr>\
											<th width='0px'></th>\
											<th width='90px'>Module name</th>\
											<th >Module details</th>\
											<th width='70px'>Operation</th>\
										</tr>\
									</thead>\
									<tbody class='modules_list'></tbody>\
								</table>\
							</div>\
						</div>\
						<div class='bt-form-submit-btn'>\
							<button type='button' class='btn btn-danger btn-sm btn-title btn-close'>" + lan.public.close + "</button>\
					        <button type='button' id='bi-btn' class='btn btn-success btn-sm btn-title bi-btn'>" + lan.public.submit + "</button>\
				        </div>\
				    </div>",
									success: function ($layer, index) {
										$layer.find('.btn-close').click(function () {
											layer.close(index);
										});
									}
                });

                $('.fangshi input').click(function() {
                    $(this).attr('checked', 'checked').parent().siblings().find("input").removeAttr('checked');
                    var type = $('.fangshi input:eq(0)').prop("checked") ? '0' : '1';
                    if (type === '1') {
                        $(".install_modules").hide();
                        return;
                    }

                    if (bt.soft.check_make_is(name)) {
                        $(".install_modules").show();
                        bt.soft.get_make_args(name);
                    }
                });

                $("#bi-btn").click(function() {
                    loadOpen.close();
                    var info = $("#SelectVersion").val().toLowerCase();
                    name = info.split(" ")[0];
                    version = info.split(" ")[1];
                    var type = $('.fangshi input:eq(0)').prop("checked") ? '0' : '1';
                    if (rdata.versions.length > 1) {
                        _this.install_soft(rdata, version, type);
                    } else {
                        _this.install_soft(rdata, rdata.versions[0].m_version, type,that);
                    }
                });
            } else if (rdata.versions.length > 1) {
                var SelectVersion = '';
                for (var i = 0; i < rdata.versions.length; i++) {
                    var item = rdata.versions[i];
                    var v_type = parseInt(item.beta) === 1 ? ' Beta' : ' Stable';
                    var version = parseInt(rdata.type) === 5 ? item.m_version : item.full_version;
                    SelectVersion += '<option>' + name + ' ' + version + v_type + '</option>';
                }
                var loadOpen = bt.open({
                    type: 1,
                    title: name + lan.soft.install_title,
                    area: '350px',
                    content: "<div class='bt-form pd20 pb70 c6'>\
						<div class='version line'>" + lan.soft.install_version + "：<select id='SelectVersion' class='bt-input-text' style='margin-left:30px'>" + SelectVersion + "</select></div>\
                        <div class='bt-form-submit-btn'>\
							<button type='button' class='btn btn-danger btn-sm btn-title' onclick='layer.closeAll()'>" + lan.public.close + "</button>\
					        <button type='button' id='bi-btn' class='btn btn-success btn-sm btn-title bi-btn'>" + lan.public.submit + "</button>\
				        </div>\
				    </div>"
                })
                $("#bi-btn").click(function() {
                    loadOpen.close();
                    var info = $("#SelectVersion").val().toLowerCase();
                    name = info.split(" ")[0];
                    version = info.split(" ")[1];
                    _this.install_soft(rdata, version, 0, that);
                });
            } else {
                _this.install_soft(rdata, parseInt(rdata.type) === 5 ? rdata.versions[0].m_version : rdata.versions[0].full_version,0,that);
            }
        })
    },
    is_loop_speed:true,
	is_install:false,
    //显示进度
    show_speed: function() {
        bt.send('get_lines', 'ajax/get_lines', {
            num: 10,
            filename: "/tmp/panelShell.pl"
        }, function(rdata) {
            if ($("#install_show").length < 1) return;
            if (rdata.status === true) {
                $("#install_show").text(rdata.msg);
                $("#install_show").scrollTop(1000000000);
            }
            setTimeout(function() { bt.soft.show_speed(); }, 1000);
        });
    },
    loadT: null,
    speed_msg: "<pre style='margin-bottom: 0px;height:250px;text-align: left;background-color: #000;color: #fff;white-space: pre-wrap;' id='install_show'>[MSG]</pre>",
    //显示进度窗口
    // show_speed_window: function(msg, callback) {
    //     bt.soft.loadT = layer.open({
    //         title: false,
    //         type: 1,
    //         closeBtn: 0,
    //         shade: 0.3,
    //         area: "500px",
    //         offset: "30%",
    //         content: bt.soft.speed_msg.replace('[MSG]', msg),
    //         success: function(layers, index) {
    //             setTimeout(function() {
    //                 bt.soft.show_speed();
    //             }, 1000);
    //             if (callback) callback();
    //         }
    //     });
    // },
    show_speed_window: function(config,callback){
		if(!config.soft) config['soft'] = {type:10}
		if(config.soft.type == 5){ //使用消息盒子安装
			if (callback) callback();
			return false;
		}else if(config.soft.type == 10 && !config.status){ //第三方安装, 非安装，仅下载安装脚本
			if (callback) callback();
			return false;
		}
		layer.closeAll();
		bt.soft.loadT = layer.open({
			title: config.title || 'Executing setup script, please wait...',
			type:1,
			closeBtn:false,
			maxmin:true,
			shade:false,
			skin:'install_soft',
			area:["500px",'300px'],
			content: "<pre style='width:500px;margin-bottom: 0px;height:100%;border-radius:0px; text-align: left;background-color: #000;color: #fff;white-space: pre-wrap;' id='install_show'>"+ config.msg +"</pre>",
			success:function(layers,index){
				$(config.event).removeAttr('onclick').html('Installing');
				$('.layui-layer-max').hide();
				bt.soft.is_loop_speed = true;
				bt.soft.is_install = true;
				bt.soft.show_speed();
				if (callback) callback();
			},
			end:function(){
				bt.soft.is_install = false;
				bt.soft.is_loop_speed = false;
			},
			min:function(){
				$('.layui-layer-max').show();
			},
			restore:function(){
				$('.layui-layer-max').hide();
			}
		});
	},
    // install_soft: function(item, version, type,that) { //安装单版本
    //     if (type == undefined) type = 0;
    //     item.title = bt.replace_all(item.title, '-' + version, '');
    //     var msg = item.type != 5 ? lan.soft.lib_insatll_confirm.replace('{1}', item.title) : lan.get('install_confirm', [item.title, version]);

    //     bt.confirm({ msg: '<div style="word-break: break-word;">'+msg+'</div>', title: item.type != 5 ? lan.soft.lib_install : lan.soft.install_title }, function() {
    //         bt.soft.show_speed_window(lan.soft.lib_install_the, function() {
    //             bt.send('install_plugin', 'plugin/install_plugin', { sName: item.name, version: version, type: type }, function(rdata) {

    //                 if (rdata.size) {
    //                     layer.close(bt.soft.loadT);
    //                     _this.install_other(rdata)
    //                     return;
    //                 }
    //                 layer.close(bt.soft.loadT);
    //                 bt.pub.get_task_count();
    //                 if (soft) soft.get_list();
    //                 bt.msg(rdata);
    //             })
    //         })
    //     })
    // },
    install_soft: function (item, version, type, that) { //安装单版本
        if (type == undefined) type = 0;
        var loadT = '';
        item.title = bt.replace_all(item.title, '-' + version, '');
        layer.confirm(item.type != 5 ? lan.soft.lib_insatll_confirm.replace('{1}', item.title) : lan.get('install_confirm', [item.title, version]), {
            btn: [lan.public.confirm, lan.public.close],
            title: item.type != 5 ? lan.soft.lib_install : lan.soft.install_title,
            icon: 0,
            closeBtn: 2
        }, function () {
            layer.closeAll();
            bt.soft.show_speed_window({
                title: 'Installing ' + item.title + ', please wait...',
                msg: lan.soft.lib_install_the,
                soft: item,
                event: that
            }, function () {
                if (item.type == 10) loadT = layer.msg('Getting third party installation information, please wait<img src="/static/img/ing.gif">', {
                    icon: 16,
                    time: 0,
                    shade: [0.3, '#000']
                });
                bt.send('install_plugin', 'plugin/install_plugin', {
                    sName: item.name,
                    version: version,
                    type: type
                }, function (rdata) {
                    if (rdata.size) {
                        layer.close(loadT);
                        bt.soft.install_other(rdata, status);
                        return;
                    }
                    layer.close(bt.soft.loadT);
						bt.pub.get_task_count(function(rdata){
							if(rdata > 0 && item.type === 5) messagebox();
						});
						if(!rdata.status){
					        layer.msg(rdata.msg, {icon: rdata.status ? 1 : 2});
					    }
						setTimeout(function(){
						    if(typeof soft != "undefined") soft.get_list();
						},2000)
					})
				})
		})
    },
    install_other: function (data) {
        layer.closeAll();
        var loadT = layer.open({
            type: 1,
            area: "500px",
            title: (data.update ? lan.public_backup.update : lan.public_backup.install) + lan.public_backup.third_party_plug,
            closeBtn: 2,
            shift: 5,
            shadeClose: false,
            btn:[data.update ? lan.public_backup.update : lan.public_backup.install,lan.public_backup.cancel],
            content: '<style>\
                        .install_three_plugin{padding:25px;}\
                        .plugin_user_info p { font-size: 14px;}\
                        .plugin_user_info {padding: 15px 30px;line-height: 26px;background: #f5f6fa;border-radius: 5px;border: 1px solid #efefef;}\
                        .btn-content{text-align: center;margin-top: 25px;}\
                    </style>\
                    <div class="bt-form c7  install_three_plugin pb70">\
                        <div class="plugin_user_info">\
                            <p><b>' + lan.public_backup.name + '</b>' + data.title + '</p>\
                            <p><b>' + lan.public_backup.version + '</b>' + data.versions + '</p>\
                            <p><b>' + lan.public_backup.ps + '</b>' + (data.update ? data.update : data.ps) + '</p>\
                            <p><b>' + lan.public_backup.size + '</b>' + bt.format_size(data.size, true) + '</p>\
                            <p><b>' + lan.public_backup.author + '</b>' + data.author + '</p>\
                            <p><b>' + lan.public_backup.source + '</b><a class="btlink" href="' + data.home + '" target="_blank">' + data.home + '</a></p>\
                        </div>\
                        <ul class="help-info-text c7">\
                            '+ (data.update ? "<li>" + lan.public_backup.update_wait + "</li>" : "<li>" + lan.public_backup.install_wait + "</li><li>" + lan.public_backup.exist_cover + "</li>")+'\
                        </ul>\
                    </div>',
            yes:function(index,event){
            	soft.input_zip(data.name,data.tmp_path,data);
            }
        });
    },
    update_soft: function(name, title, version, min_version, update_msg,type) {
        var _this = this;
        var msg = "<li>" + lan.public_backup.update_tips + "</li>";
        if (name == 'mysql') msg = "<ul style='color:red;'><li>" + lan.public_backup.db_update_tips + "</li><li>" + lan.public_backup.update_tips1 + "</li><li>" + lan.public_backup.update_tips + "</li></ul>";
        if (update_msg) msg += '<div style="    margin-top: 10px;"><span style="font-size: 14px;font-weight: 900;">Update description: </span><hr style="margin-top: 5px; margin-bottom: 5px;" /><pre>' + update_msg.replace(/(_bt_)/g, "\n") + '</pre><hr style="margin-top: -5px; margin-bottom: -5px;" /></div>';
        bt.show_confirm(lan.public_backup.update + '[' + title + ']', lan.public_backup.update_tips2.replace('{1}', title).replace('{2}', version).replace('{3}', min_version), function() {
            // bt.soft.show_speed_window('Updating to [' + title + '-' + version + '.' + min_version + '],Please wait...', function() {
            //     bt.send('install_plugin', 'plugin/install_plugin', { sName: name, version: version, upgrade: version }, function(rdata) {
            //         if (rdata.size) {
            //             _this.install_other(rdata)
            //             return;
            //         }
            //         layer.close(bt.soft.loadT);
            //         bt.pub.get_task_count(function(rdata){
			// 			if(rdata > 0 && item.type === 5) messagebox();
			// 		});
            //         if (soft) soft.get_list();
            //         if (rdata.status === true && rdata.msg.indexOf('queue') === -1) rdata.msg = 'Update completed!';
            //         bt.msg(rdata);
            //     })
            // })
             _this.get_soft_find(name, function (item) {
                 var full_version = parseInt(item.type) === 5 ? version : (version+'.'+min_version);
                 bt.soft.show_speed_window({title:'Updating to [' + title+'-'+version+'.'+min_version+'],Please wait...',status:true,soft:{type:parseInt(type)}},function(){
                    bt.send('install_plugin', 'plugin/install_plugin', { sName: name, version: full_version, upgrade: full_version }, function (rdata) {
                        console.log(rdata);
                        if (rdata.size) {
                            _this.install_other(rdata)
                            return;
                        }
                        layer.close(bt.soft.loadT);
                        bt.pub.get_task_count(function(rdata){
                            if(rdata > 0 && parseInt(item.type) === 5) messagebox();
                        });
                        if(typeof soft != "undefined") soft.get_list();
                        bt.msg(rdata);
                    });
                });
             });
        }, msg);
    },
    un_install: function(name) {
        var _this = this;
        _this.get_soft_find(name, function(item) {
            var version = '';
            for (var i = 0; i < item.versions.length; i++) {
                if (item.versions[i].setup && bt.contains(item.version, item.versions[i].m_version)) {
                    version = item.versions[i].m_version;
                    if (version.indexOf('.') < 0) version += '.' + item.versions[i].version;
                    break;
                }
            }
            var title = bt.replace_all(item.title, '-' + version, '');
            bt.confirm({ msg: lan.soft.uninstall_confirm.replace('{1}', title).replace('{2}', version), title: lan.soft.uninstall, icon: 3, closeBtn: 2 }, function() {
                var loadT = bt.load(lan.soft.lib_uninstall_the);
                bt.send('uninstall_plugin', 'plugin/uninstall_plugin', { sName: name, version: version }, function(rdata) {
                    loadT.close();
                    bt.pub.get_task_count();
                    if (soft) soft.get_list();
                    bt.msg(rdata);
                })
            })
        })

    },
    get_soft_find: function(name, callback) {
        var loadT = bt.load();
        bt.send('get_soft_find', 'plugin/get_soft_find', { sName: name }, function(rdata) {
            loadT.close();
            if (callback) callback(rdata);
        })
    },
    get_config_path: function(name) {
        var fileName = '';
        if (bt.os == 'Linux') {
            switch (name) {
                case 'mysql':
                case 'mysqld':
                    fileName = '/etc/my.cnf';
                    break;
                case 'nginx':
                    fileName = '/www/server/nginx/conf/nginx.conf';
                    break;
                case 'pureftpd':
                    fileName = '/www/server/pure-ftpd/etc/pure-ftpd.conf';
                    break;
                case 'apache':
                    fileName = '/www/server/apache/conf/httpd.conf';
                    break;
                case 'tomcat':
                    fileName = '/www/server/tomcat/conf/server.xml';
                    break;
                case 'memcached':
                    fileName = '/etc/init.d/memcached';
                    break;
                case 'redis':
                    fileName = '/www/server/redis/redis.conf';
                    break;
                case 'openlitespeed':
                    fileName = '/usr/local/lsws/conf/httpd_config.conf';
                    break;
                default:
                    fileName = '/www/server/php/' + name + '/etc/php.ini';
                    break;
            }
        }
        return fileName
    },
    set_lib_config: function(name, title) {
        var loadT = bt.load(lan.soft.menu_temp);
        bt.send('getConfigHtml', 'plugin/getConfigHtml', { name: name }, function(rhtml) {
            loadT.close();
            if (rhtml.status === false) {
                if (name == "phpguard") {
                    layer.msg(lan.soft.menu_phpsafe, { icon: 1 })
                } else {
                    layer.msg(rhtml.msg, { icon: 2 });
                }
                return;
            }
            bt.open({
                type: 1,
                shift: 5,
                offset: '20%',
                closeBtn: 2,
                area: '700px',
                title: '' + title,
                content: rhtml.replace('"javascript/text"', '"text/javascript"')
            });
            /*rtmp = rhtml.split('<script type="javascript/text">')
            if (rtmp.length < 2) {
                rtmp = rhtml.split('<script type="text/javascript">')
            }
            rcode = rtmp[1].replace('</script>','');
			setTimeout(function(){
				if(!!(window.attachEvent && !window.opera)){
                    execScript(rcode);
				}else{
                    window.eval(rcode);
				}
			},200)*/
        });
    },
    save_config: function(fileName, data) {
        var encoding = 'utf-8';
        var loadT = bt.load(lan.soft.the_save);
        bt.send('SaveFileBody', 'files/SaveFileBody', { data: data, path: fileName, encoding: encoding }, function(rdata) {
            loadT.close();
            bt.msg(rdata);
        })
    }

}


bt.database = {
    get_list: function(page, search, callback) {
        if (page == undefined) page = 1
        search = search == undefined ? '' : search;
        var order = bt.get_cookie('order') ? '&order=' + bt.get_cookie('order') : '';

        var data = 'tojs=database.get_list&table=databases&limit=15&p=' + page + '&search=' + search + order;
        bt.pub.get_data(data, function(rdata) {
            if (callback) callback(rdata);
        })
    },
    get_root_pass: function(callback) {
        bt.send('getKey', 'data/getKey', { table: 'config', key: 'mysql_root', id: 1 }, function(rdata) {
            if (callback) callback(rdata);
        })
    },
    set_root: function(type) {
			if(type == 'mongo' || type == 'pgsql') {
				var t = bt.data.database.getType();
				bt_tools.send('database/' + t + '/get_root_pwd', function (rdata) {
					if (type == 'pgsql') bt.data.database.mongo['list'][0]['title'] = lan.database.admin_password;
					var bs = bt.render_form(bt.data.database.mongo);
					$('.password' + bs).val(rdata.msg);
				});				
			} else {
				bt.database.get_root_pass(function(rdata) {
					var bs = bt.render_form(bt.data.database.root);
					$('.password' + bs).val(rdata);
				});
			}
    },
    set_data_pass: function(callback) {
			var bs = bt.render_form(bt.data.database.data_pass, function(rdata) {
				if (callback) callback(rdata);
			});
			return bs;
    },
    set_data_access: function(name) {
        var loading = bt.load();
        bt.send('GetDatabaseAccess', 'database/GetDatabaseAccess', { name: name }, function(rdata) {
            loading.close();
            var bs = bt.render_form(bt.data.database.data_access);
            $('.name' + bs).val(name);
            $('.bt-form .line .tname').css('width','125px');
            setTimeout(function() {
                if (rdata.msg.permission == '127.0.0.1' || rdata.msg.permission == '%') {
                    $('.dataAccess' + bs).val(rdata.msg.permission)
                } else {
                    $('.dataAccess' + bs).val('ip').trigger('change');
                    $('#dataAccess_subid').val(rdata.msg.permission);
                }
                $("#force_ssl").prop('checked', rdata.msg.ssl ? true : false);
                $("#force_ssl").change(function() {
                    var open_type = $("#force_ssl").prop('checked');
                    if (open_type) {
                        var t = '<div>\
                                <h3 style="font-size: 18px;font-weight:600;">Warning! This feature requires Advanced Knowledge!</h3>\
                                <ul style="width:91%;margin-top: 19px;border: 1px solid #ececec;border-radius: 10px;background: #f7f7f7;padding: 15px;list-style-type: inherit;padding-left:25px;">\
                                    <li style="color:red;">After enabling the forced SSL connection, it may affect your application connection and database performance.</li>\
                                </ul>\
                        </div>';
                        var loadP = layer.confirm(t, {
                            btn: ['Confirm', 'Cancel'],
                            icon: 3,
                            area: '561px',
                            closeBtn: 2,
                            title: 'Confirm Open?'
                        }, function() {
                            $("#force_ssl").prop('checked',true);
                            layer.close(loadP);
                        }, function() {
                            $("#force_ssl").prop('checked',false);
                            layer.close(loadP);
                        });
                    }
                });
            }, 100)
        })
    },
    add_database: function(cloudList, callback) {
			var type = bt.data.database.getType();
			if (type === 'mysql') {
        bt.data.database.data_add.list[2].items[0].value = bt.get_random(16);
        bt.data.database.data_add.list[4].items[0].items = cloudList;
        bt.render_form(bt.data.database.data_add, function(rdata) {
					if (callback) callback(rdata);
        });
			} else {
				var copyDataAdd = $.extend(true, {}, bt.data.database.data_add);
				copyDataAdd.list[2].items[0].value = bt.get_random(16);
				switch (type) {
					case 'sqlserver':
					case 'mongodb':
					case 'pgsql':
						delete copyDataAdd.list[0].items[1]
						copyDataAdd.list.splice(3)
						copyDataAdd.list.push(bt.data.database.data_add.list[4])
						copyDataAdd.list.push(bt.data.database.data_add.list[5])
						copyDataAdd.list[3].items[0].items = cloudList;
						break;
				}
				// 没有本地或者远程数据库
				if (cloudList.length == 0) {
					copyDataAdd.list[copyDataAdd.list.length - 1].hide = true;
				}
				bt.render_form($.extend(true, {}, copyDataAdd), function (rdata) {
					if (callback) callback(rdata);
				});
			}
    },
    del_database: function(data, callback) {
			var loadT = bt.load(lan.get('del_all_task_the', [data.name]));
			var type = bt.data.database.getType();
			var params = { url: 'database?action=DeleteDatabase', data: data }
			if (type != 'mysql') {
				params.url = 'database/' + type + '/DeleteDatabase';
				params.data = { data: JSON.stringify(data) };
			}
			bt_tools.send(params, function(rdata) {
				loadT.close();
				bt.msg(rdata);
				if (callback) callback(rdata);
			})
    },
    sync_database: function(sid, callback) {
			var loadT = bt.load(lan.database.sync_the);
			var type = bt.data.database.getType();
			var params = { url: 'database?action=SyncGetDatabases', data: { sid: sid } }
			if (type != 'mysql') {
				params.url = 'database/' + type + '/SyncGetDatabases';
				params.data = { data: JSON.stringify({ sid: sid }) };
			}
			bt_tools.send(params, function (rdata) {
				loadT.close();
				bt.msg(rdata);
				if (callback) callback(rdata);
			});
    },
    sync_to_database: function(data, callback) {
			var loadT = bt.load(lan.database.sync_the);
			var type = bt.data.database.getType();
			var params = { url: 'database?action=SyncToDatabases', data: data }
			if (type != 'mysql') {
				params.url = 'database/' + type + '/SyncToDatabases';
				params.data = { data: JSON.stringify(data) };
			}
			bt_tools.send(params, function(rdata) {
				loadT.close();
				if (callback) callback(rdata);
				bt.msg(rdata);
			})
    },
    open_phpmyadmin:function(name,username,password){

		if($("#toPHPMyAdmin").attr('action').indexOf('phpmyadmin') == -1){
		layer.msg(lan.database.phpmyadmin_err,{icon:2,shade: [0.3, '#000']})
		setTimeout(function(){ window.location.href = '/soft'; },3000);
			return;
		}
		$("#toPHPMyAdmin").attr('action',$("#toPHPMyAdmin").attr('public-data'))
		var murl = $("#toPHPMyAdmin").attr('action');
		$("#pma_username").val(username);
		$("#pma_password").val(password);
		$("#db").val(name);
		layer.msg(lan.database.phpmyadmin,{icon:16,shade: [0.3, '#000'],time:1000});
		setTimeout(function(){
			$("#toPHPMyAdmin").submit();
			layer.closeAll();
		},200);
	},
	submit_phpmyadmin: function(name,username,password,pub){
		if(pub === true){
			$("#toPHPMyAdmin").attr('action',$("#toPHPMyAdmin").attr('public-data'))
		}else{
			$("#toPHPMyAdmin").attr('action','/phpmyadmin/index.php')
		}
		var murl = $("#toPHPMyAdmin").attr('action');
		$("#pma_username").val(username);
		$("#pma_password").val(password);
		$("#db").val(name);
		layer.msg(lan.database.phpmyadmin,{icon:16,shade: [0.3, '#000'],time:1000});
		setTimeout(function(){
			$("#toPHPMyAdmin").submit();
			layer.closeAll();
		},200);
	},
    input_sql: function(fileName, dataName) {
			bt.confirm({ msg: lan.database.input_confirm, title: lan.database.input_title }, function(index) {
				var loading = bt.load(lan.database.input_the);
				var type = bt.data.database.getType();
				var params = { url: 'database?action=InputSql', data: { file: fileName, name: dataName } }
				if (type != 'mysql') {
					params.url = 'database/' + type + '/InputSql';
					params.data = { data: JSON.stringify({ file: fileName, name: dataName }) };
				}
				bt_tools.send(params, function(rdata) {
					loading.close();
					bt.msg(rdata);
				})
			});
    },
    backup_data: function(id, callback) {
			var loadT = bt.load(lan.database.backup_the);
			var type = bt.data.database.getType();
			var params = { url: 'database?action=ToBackup', data: { id: id } }
			if (type != 'mysql') {
				params.url = 'database/' + type + '/ToBackup';
				params.data = { data: JSON.stringify({ id: id }) };
			}
			bt_tools.send(params, function(rdata) {
				loadT.close();
				bt.msg(rdata);
				if (callback) callback(rdata);
			});
    },
    del_backup: function(id, success, error) {
			bt.confirm({ msg: lan.database.backup_del_confirm, title: lan.database.backup_del_title }, function(index) {
				var loadT = bt.load();
				bt.send('DelBackup', 'database/DelBackup', { id: id }, function(frdata) {
					loadT.close();
					bt.msg(frdata);
					if (frdata.status) {
						success && success(frdata);
					} else {
						error && error(frdata);
					}
				});
			});
    }
}

bt.send('get_config', 'config/get_config', {}, function(rdata) {
    bt.config = rdata;
})

bt.plugin = {
    get_plugin_byhtml: function(name, callback) {
        bt.send('getConfigHtml', 'plugin/getConfigHtml', { name: name }, function(rdata) {
            if (callback) callback(rdata);
        });
    },
    get_firewall_state: function(callback) {
        var typename = getCookie('serverType');
        var name = 'btwaf_httpd';
        if (typename == "nginx") name = 'btwaf'
        bt.send('a', 'plugin/a', { name: name, s: 'get_total_all' }, function(rdata) {
            if (callback) callback(rdata);
        })
    }
}

bt.site = {
    get_list: function(page, search, type, callback) {
        if (page == undefined) page = 1
        type = type == undefined ? '&type=-1' : ('&type=' + type);
        search = search == undefined ? '' : search;
        var order = bt.get_cookie('order') ? '&order=' + bt.get_cookie('order') : '';
        var data = 'tojs=site.get_list&table=sites&limit=15&p=' + page + '&search=' + search + order + type;
        bt.pub.get_data(data, function(rdata) {
            if (callback) callback(rdata);
        })
    },
    get_domains: function(id, callback) {
        var data = 'table=domain&list=True&search=' + id;
        bt.pub.get_data(data, function(rdata) {
            if (callback) callback(rdata);
        }, 1)
    },
    get_type: function(callback) {
        bt.send('get_site_types', 'site/get_site_types', '', function(rdata) {
            if (callback) callback(rdata);
        });
    },
    add_type: function(name, callback) {
        bt.send('add_site_type', 'site/add_site_type', { name: name }, function(rdata) {
            if (callback) callback(rdata);
        });
    },
    edit_type: function(data, callback) {
        bt.send('modify_site_type_name', 'site/modify_site_type_name', { id: data.id, name: data.name }, function(rdata) {
            if (callback) callback(rdata);
        });
    },
    del_type: function(id, callback) {
        bt.send('remove_site_type', 'site/remove_site_type', { id: id }, function(rdata) {
            if (callback) callback(rdata);
        });
    },
    set_site_type: function(data, callback) {
        bt.send('set_site_type', 'site/set_site_type', { id: data.id, site_ids: data.site_array }, function(rdata) {
            if (callback) callback(rdata);
        });
    },
    get_site_domains: function(id, callback) {
        var loading = bt.load();
        bt.send('GetSiteDomains', 'site/GetSiteDomains', { id: id }, function(rdata) {
            loading.close();
            if (callback) callback(rdata);
        })
    },
    add_domains: function(id, webname, domains, callback) {
        var loading = bt.load();
        bt.send('AddDomain', 'site/AddDomain', { domain: domains, webname: webname, id: id }, function(rdata) {
            loading.close();
            if (callback) callback(rdata);
            bt.msg(rdata);
        })
    },
    del_domain: function(siteId, siteName, domain, port, callback) {
        var loading = bt.load();
        bt.send('DelDomain', 'site/DelDomain', { id: siteId, webname: siteName, domain: domain, port: port }, function(rdata) {
            loading.close();
            if (callback) callback(rdata);
            bt.msg(rdata);
        })
    },
    get_dirbind: function(id, callback) {
        var loading = bt.load();
        bt.send('GetDirBinding', 'site/GetDirBinding', { id: id }, function(rdata) {
            loading.close();
            if (callback) callback(rdata);
        })
    },
    add_dirbind: function(id, domain, dirName, callback) {
        var loading = bt.load();
        bt.send('AddDirBinding', 'site/AddDirBinding', { id: id, domain: domain, dirName: dirName }, function(rdata) {
            loading.close();
            if (callback) callback(rdata);
        })
    },
    del_dirbind: function(id, callback) {
        var loading = bt.load();
        bt.send('DelDirBinding', 'site/DelDirBinding', { id: id}, function(rdata) {
            loading.close();
            if (callback) callback(rdata);
        })
    },
    get_dir_rewrite: function(data, callback) {
        var loading = bt.load();
        bt.send('GetDirRewrite', 'site/GetDirRewrite', data, function(rdata) {
            loading.close();
            if (callback) callback(rdata);
        })
    },
    get_site_path: function(id, callback) {
        bt.send('getKey', 'data/getKey', { table: 'sites', key: 'path', id: id }, function(rdata) {
            if (callback) callback(rdata);
        })
    },
    get_dir_userini: function(id, path, callback) {
        bt.send('GetDirUserINI', 'site/GetDirUserINI', { id: id, path: path }, function(rdata) {
            if (callback) callback(rdata);
        })
    },
    set_dir_userini: function(path, id, callback) {
        var loading = bt.load();
        bt.send('SetDirUserINI', 'site/SetDirUserINI', { path: path, id: id }, function(rdata) {
            loading.close();
            if (callback) callback(rdata);
        })
    },
    set_logs_status: function(id, callback) {
        var loading = bt.load();
        bt.send('logsOpen', 'site/logsOpen', { id: id }, function(rdata) {
            loading.close();
            if (callback) callback(rdata);
        })
    },
    set_site_runpath: function(id, path, callback) {
        var loading = bt.load();
        bt.send('SetSiteRunPath', 'site/SetSiteRunPath', { id: id, runPath: path }, function(rdata) {
            loading.close();
            if (callback) callback(rdata);
        })
    },
    set_site_path: function(id, path, callback) {
        var loading = bt.load();
        bt.send('SetPath', 'site/SetPath', { id: id, path: path }, function(rdata) {
            loading.close();
            if (callback) callback(rdata);
        })
    },
    set_site_path_new: function(id, path, name, callback) {
        var loading = bt.load();
        bt.send('SetPath', 'site/SetPath', { id: id, path: path , name:name }, function(rdata) {
            loading.close();
            if (callback) callback(rdata);
        })
    },
    set_site_pwd: function(id, username, password, callback) {
        var loading = bt.load();
        bt.send('SetHasPwd', 'site/SetHasPwd', { id: id, username: username, password: password }, function(rdata) {
            loading.close();
            if (callback) callback(rdata);
        })
    },
    close_site_pwd: function(id, callback) {
        var loading = bt.load();
        bt.send('SetHasPwd', 'site/CloseHasPwd', { id: id }, function(rdata) {
            loading.close();
            if (callback) callback(rdata);
        })
    },
    get_limitnet: function(id, callback) {
        bt.send('GetLimitNet', 'site/GetLimitNet', { id: id }, function(rdata) {
            if (callback) callback(rdata);
        })
    },
    set_limitnet: function(id, perserver, perip, limit_rate, callback) {
        var loading = bt.load();
        bt.send('SetLimitNet', 'site/SetLimitNet', { id: id, perserver: perserver, perip: perip, limit_rate: limit_rate }, function(rdata) {
            loading.close();
            if (callback) callback(rdata);
        })
    },
    close_limitnet: function(id, callback) {
        var loading = bt.load();
        bt.send('CloseLimitNet', 'site/CloseLimitNet', { id: id }, function(rdata) {
            loading.close();
            if (callback) callback(rdata);
        })
    },
    get_rewrite_list: function(siteName, callback) {
        bt.send('GetRewriteList', 'site/GetRewriteList', { siteName: siteName }, function(rdata) {
            if (callback) callback(rdata);
        })
    },
    set_rewrite_tel: function(name, data, callback) {
        var loading = bt.load(lan.site.saving_txt);
        bt.send('SetRewriteTel', 'site/SetRewriteTel', { name: name, data: data }, function(rdata) {
            loading.close();
            if (callback) callback(rdata);
        })
    },
    get_index: function(id, callback) {
        bt.send('GetIndex', 'site/GetIndex', { id: id }, function(rdata) {
            if (callback) callback(rdata);
        })
    },
    set_index: function(id, index, callback) {
        var loading = bt.load();
        bt.send('SetIndex', 'site/SetIndex', { id: id, Index: index }, function(rdata) {
            loading.close();
            if (callback) callback(rdata);
        })
    },
    get_site_config: function(siteName, callback) {
        if (bt.os == 'Linux') {
            var sPath = '/www/server/panel/vhost/' + bt.get_cookie('serverType') + '/' + siteName + '.conf';
            bt.files.get_file_body(sPath, function(rdata) {
                if (callback) callback(rdata);
            })
        }
    },
    set_site_config: function(siteName, data, encoding, callback) {
        var loading = bt.load(lan.site.saving_txt);
        if (bt.os == 'Linux') {
            var sPath = '/www/server/panel/vhost/' + bt.get_cookie('serverType') + '/' + siteName + '.conf';
            bt.files.set_file_body(sPath, data, 'utf-8', function(rdata) {
                loading.close();
                if (callback) callback(rdata);
            })
        }
    },
    set_phpversion: function(siteName, version, other, callback) {
        var loading = bt.load();
        bt.send('SetPHPVersion', 'site/SetPHPVersion', { siteName: siteName, version: version, other: other }, function(rdata) {
            loading.close();
            if (callback) callback(rdata);
        })
    },
    // 重定向列表
    get_redirect_list: function(name, callback) {
        var loadT = bt.load(lan.site.the_msg);
        bt.send('GetRedirectList', 'site/GetRedirectList', { sitename: name }, function(rdata) {
            loadT.close();
            if (callback) callback(rdata);
        });
    },
    // 重定向列表
    get_redirect_list: function(name, callback) {
        var loadT = layer.load();
        bt.send('GetRedirectList', 'site/GetRedirectList', { sitename: name }, function(rdata) {
            layer.close(loadT);
            if (callback) callback(rdata);
        });
    },
    create_redirect: function(obj, callback) {
        var loadT = bt.load(lan.site.the_msg);
        bt.send('CreateRedirect', 'site/CreateRedirect', obj, function(rdata) {
            loadT.close();
            if (callback) callback(rdata);
        });
    },
    modify_redirect: function(obj, callback) {
        var loadT = bt.load(lan.site.the_msg);
        bt.send('ModifyRedirect', 'site/ModifyRedirect', obj, function(rdata) {
            loadT.close();
            if (callback) callback(rdata);
        });
    },
    remove_redirect: function(sitename, redirectname, callback) {
        bt.show_confirm(lan.public_backup.del_rep + '[' + redirectname + ']', lan.public_backup.sure_del_rep, function() {
            var loadT = bt.load(lan.site.the_msg);
            bt.send('DeleteRedirect', 'site/DeleteRedirect', { sitename: sitename, redirectname: redirectname }, function(rdata) {
                loadT.close();
                if (callback) callback(rdata);
            });
        });
    },
    get_redirect_config: function(obj, callback) {
        var loadT = bt.load(lan.site.the_msg);
        bt.send('GetRedirectFile', 'site/GetRedirectFile', obj, function(rdata) {
            loadT.close();
            if (callback) callback(rdata);
        });
    },
    save_redirect_config: function(obj, callback) {
        var loadT = bt.load(lan.site.the_msg);
        bt.send('SaveProxyFile', 'site/SaveRedirectFile', obj, function(rdata) {
            loadT.close();
            if (callback) callback(rdata);
        });
    },
    get_site_proxy: function(siteName, callback) {
        bt.send('GetProxy', 'site/GetProxy', { name: siteName }, function(rdata) {
            if (callback) callback(rdata);
        })
    },
    set_site_proxy: function(siteName, type, proxyUrl, toDomain, sub1, sub2, callback) {
        var loading = bt.load();
        bt.send('SetProxy', 'site/SetProxy', { name: siteName, type: type, proxyUrl: proxyUrl, toDomain: toDomain, sub1: sub1, sub2: sub2 }, function(rdata) {
            loading.close();
            if (callback) callback(rdata);
        })
    },
    set_open_proxy_cache: function(siteName, callback) {
        var loading = bt.load();
        bt.send('ProxyCache', 'site/ProxyCache', { siteName: siteName }, function(rdata) {
            loading.close();
            if (callback) callback(rdata);
        })
    },
    get_proxy_list: function(name, callback) {
        var loadT = bt.load(lan.site.the_msg);
        bt.send('GetProxyList', 'site/GetProxyList', { sitename: name }, function(rdata) {
            loadT.close();
            if (callback) callback(rdata);
        })
    },
    create_proxy: function(obj, callback) {
        var loadT = bt.load(lan.site.the_msg);
        bt.send('CreateProxy', 'site/CreateProxy', obj, function(rdata) {
            loadT.close();
            if (callback) callback(rdata);
        });
    },
    remove_proxy: function(sitename, proxyname, callback) {
        bt.show_confirm(lan.public_backup.del_proxy + '[' + proxyname + ']', lan.public_backup.sure_del_proxy, function() {
            var loadT = bt.load(lan.site.the_msg);
            bt.send('RemoveProxy', 'site/RemoveProxy', { sitename: sitename, proxyname: proxyname }, function(rdata) {
                loadT.close();
                if (callback) callback(rdata);
                bt.msg(rdata);
            })
        })
    },
    modify_proxy: function(obj, callback) {
        var loadT = bt.load(lan.site.the_msg);
        bt.send('ModifyProxy', '	site/ModifyProxy', obj, function(rdata) {
            loadT.close();
            if (callback) callback(rdata);
        });
    },
    get_proxy_config: function(obj, callback) {
        var loadT = bt.load(lan.site.the_msg);
        bt.send('GetProxyFile', 'site/GetProxyFile', obj, function(rdata) {
            loadT.close();
            if (callback) callback(rdata);
        });
    },
    save_proxy_config: function(obj, callback) {
        var loadT = bt.load(lan.site.the_msg);
        bt.send('SaveProxyFile', 'site/SaveProxyFile', obj, function(rdata) {
            loadT.close();
            if (callback) callback(rdata);
        });
    },
    get_site_security: function(id, name, callback) {
        bt.send('GetSecurity', 'site/GetSecurity', { id: id, name: name }, function(rdata) {
            if (callback) callback(rdata);
        })
    },
    set_site_security: function(id, name, fix, domains, status, return_rule, callback) {
        var loading = bt.load(lan.site.the_msg);
        bt.send('SetSecurity', 'site/SetSecurity', { id: id, name: name, fix: fix, domains: domains, status: status, return_rule:return_rule }, function(rdata) {
            loading.close();
            if (callback) callback(rdata);
        })
    },
    get_site_301: function(siteName, callback) {
        bt.send('Get301Status', 'site/Get301Status', { siteName: siteName }, function(rdata) {
            if (callback) callback(rdata);
        })
    },
    set_site_301: function(siteName, srcDomain, toUrl, type, callback) {
        var loading = bt.load();
        bt.send('Set301Status', 'site/Set301Status', { siteName: siteName, toDomain: toUrl, srcDomain: srcDomain, type: type }, function(rdata) {
            loading.close();
            if (callback) callback(rdata);
        })
    },
    set_tomcat: function(siteName, callback) {
        var loading = bt.load(lan.public.config);
        bt.send('SetTomcat', 'site/SetTomcat', { siteName: siteName }, function(rdata) {
            loading.close();
            if (callback) callback(rdata);
        })
    },
    get_site_logs: function(siteName, callback) {
        var loading = bt.load();
        bt.send('GetSiteLogs', 'site/GetSiteLogs', { siteName: siteName }, function(rdata) {
            loading.close();
            if (rdata.status !== true) rdata.msg = '';
            if (rdata.msg == '') rdata.msg = lan.public_backup.no_log;
            if (callback) callback(rdata);
        })
    },
    get_site_error_logs: function (siteName, callback) {
      var loading = bt.load();
      bt.send('get_site_err_log', 'site/get_site_err_log', {
        siteName: siteName
        }, function (rdata) {
            loading.close();
            if (rdata.status !== true) rdata.msg = '';
            if (rdata.msg == '') rdata.msg = lan.public_backup.no_log;
            if (callback) callback(rdata);
        })
      },
    get_site_ssl: function(siteName, callback) {
        var loadT = bt.load(lan.site.the_msg);
        bt.send('GetSSL', 'site/GetSSL', { siteName: siteName }, function(rdata) {
            loadT.close();
            if (callback) callback(rdata);
        });
    },
    create_let: function(data, callback) {
        var loadT = layer.open({
            title: false,
            type: 1,
            closeBtn: 0,
            shade: 0.3,
            area: "500px",
            offset: "30%",
            content: "<pre style='margin-bottom: 0px;height:250px;text-align: left;background-color: #000;color: #fff;white-space: pre-wrap;' id='create_lst'>" + lan.public_backup.preparing_for_cert + "...</pre>",
            success: function(layers, index) {
                bt.site.get_let_logs();
                bt.send('CreateLet', 'site/CreateLet', data, function(rdata) {
                    layer.close(loadT);
                    if (callback) callback(rdata);
                });
            }
        });
    },
    get_let_logs: function() {
        bt.send('get_lines', 'ajax/get_lines', {
            num: 10,
            filename: "/www/server/panel/logs/letsencrypt.log"
        }, function(rdata) {
            if ($("#create_lst").text() === "") return;
            if (rdata.status === true) {
                $("#create_lst").text(rdata.msg);
                $("#create_lst").scrollTop($("#create_lst")[0].scrollHeight);
            }
            setTimeout(function() { bt.site.get_let_logs(); }, 1000);
        });
    },
    get_dns_api: function(callback) {
        var loadT = bt.load();
        bt.send('GetDnsApi', 'site/GetDnsApi', {}, function(rdata) {
            loadT.close();
            if (callback) callback(rdata);
        })
    },
    set_dns_api: function(data, callback) {
        var loadT = bt.load();
        bt.send('SetDnsApi', 'site/SetDnsApi', data, function(rdata) {
            loadT.close();
            if (callback) callback(rdata);
        })
    },
    verify_domain: function(partnerOrderId, siteName, callback) {
        var loadT = bt.load(lan.site.ssl_apply_2);
        bt.send('Completed', 'ssl/Completed', { partnerOrderId: partnerOrderId, siteName: siteName }, function(rdata) {
            loadT.close();
            if (callback) callback(rdata);
        })
    },
    get_dv_ssl: function(domain, path, callback) {
        var loadT = bt.load(lan.site.ssl_apply_1);
        bt.send('GetDVSSL', 'ssl/GetDVSSL', { domain: domain, path: path }, function(rdata) {
            loadT.close();
            if (callback) callback(rdata);
        })
    },
get_module_config: function (param, callback) {
			var loadT = bt.load('Obtaining the alarm configuration, please wait...');
			bt.send(
				'get_module_config',
				'push/get_module_config',
				{
					name: param.name,
					type: param.type,
				},
				function (rdata) {
					loadT.close();
					if (callback) callback(rdata);
				}
			);
		},

		// 设置
		set_push_config: function (param, callback) {
			var loadT = bt.load('Please wait while setting alarm configuration...');
			bt.send(
				'set_push_config',
				'push/set_push_config',
				{
					name: param.name,
					id: param.id,
					data: param.data,
				},
				function (rdata) {
					loadT.close();
					if (callback) callback(rdata);
				}
			);
		},
		// 获取消息推送配置
		get_msg_configs: function (callback) {
			var loadT = bt.load('Getting the message push configuration, please wait...');
			bt.send('get_msg_configs', 'config/get_msg_configs', {}, function (rdata) {
				loadT.close();
				if (callback) callback(rdata);
			});
		},
		// 下载证书
		download_cert: function (param, callback) {
			var loadT = bt.load('Please wait while downloading the certificate...');
			bt.send(
				'download_cert',
				'site/download_cert',
				{
					siteName: param.siteName,
					ssl_type: param.ssl_type || 'csr',
					pem: param.pem,
					key: param.key,
					pwd: param.pwd || '', //密码，非必填
				},
				function (rdata) {
					loadT.close();
					if (callback) callback(rdata);
				}
			);
		},
    get_ssl_info: function(partnerOrderId, siteName, callback) {
        var loadT = bt.load(lan.site.ssl_apply_3);
        bt.send('GetSSLInfo', 'ssl/GetSSLInfo', { partnerOrderId: partnerOrderId, siteName: siteName }, function(rdata) {
            loadT.close();
            if (callback) callback(rdata);
        })
    },
    set_cert_ssl: function(certName, siteName, callback) {
        var loadT = bt.load(lan.public_backup.deploy_cert);
        bt.send('SetCertToSite', 'ssl/SetCertToSite', { certName: certName, siteName: siteName }, function(rdata) {
            loadT.close();
            site.reload();
            if (callback) callback(rdata);
            bt.msg(rdata);
        })
    },
    remove_cert_ssl: function(certName, callback) {
        bt.show_confirm(lan.public_backup.del_cert, lan.public_backup.sure_del_cert, function() {
            var loadT = bt.load(lan.site.the_msg);
            bt.send('RemoveCert', 'ssl/RemoveCert', { certName: certName }, function(rdata) {
                loadT.close();
                if (callback) callback(rdata);
                bt.msg(rdata);
            })
        })
    },
    set_http_to_https: function(siteName, callback) {
        var loading = bt.load();
        bt.send('HttpToHttps', 'site/HttpToHttps', { siteName: siteName }, function(rdata) {
            loading.close();
            if (callback) callback(rdata);
            bt.msg(rdata);
        })
    },
    close_http_to_https: function(siteName, callback) {
        var loading = bt.load();
        bt.send('CloseToHttps', 'site/CloseToHttps', { siteName: siteName }, function(rdata) {
            loading.close();
            if (callback) callback(rdata);
            bt.msg(rdata);
        })
    },
    set_ssl: function(siteName, data, callback) {
        if (data.path) {
            //iis导入证书
        } else {
            var loadT = bt.load(lan.site.saving_txt);
            bt.send('SetSSL', 'site/SetSSL', { type: 1, siteName: siteName, key: data.key, csr: data.csr }, function(rdata) {
                loadT.close();
                if (callback) callback(rdata);
            })
        }
    },
    set_ssl_status: function(action, siteName, callback) {
        var loadT = bt.load(lan.site.get_ssl_list);
        bt.send(action, 'site/' + action, { updateOf: 1, siteName: siteName }, function(rdata) {
            loadT.close();
            if (callback) callback(rdata);
        })
    },
    get_cer_list: function(callback) {
        var loadT = bt.load(lan.site.the_msg);
        bt.send('GetCertList', 'ssl/GetCertList', {}, function(rdata) {
            loadT.close();
            if (callback) callback(rdata);
        })
    },
    get_order_list: function(siteName, callback) {
        bt.send('GetOrderList', 'ssl/GetOrderList', { siteName: siteName }, function(rdata) {
            if (callback) callback(rdata);
        })
    },
    del_site: function(data, callback) {
        var loadT = bt.load(lan.get('del_all_task_the', [data.webname]));
        bt.send('DeleteSite', 'site/DeleteSite', data, function(rdata) {
            loadT.close();
            if (callback) callback(rdata);
        })
    },
    add_site: function(callback) {
        var _form = $.extend(true, {}, bt.data.site.add);
        bt.site.get_all_phpversion(function(rdata) {
            bt.site.get_type(function(tdata) {
                for (var i = 0; i < _form.list.length; i++) {
                    if (_form.list[i].name == 'version') {
                        var items = [];
                        for (var j = rdata.length - 1; j >= 0; j--) {
                            var o = rdata[j];
                            o.value = o.version;
                            o.title = o.name;
                            items.push(o);
                        }
                        _form.list[i].items = items;
                    } else if (_form.list[i].name == 'type_id') {
                        for (var x = 0; x < tdata.length; x++) _form.list[i].items.push({ value: tdata[x].id, title: tdata[x].name });
                    }
                }
                var bs = bt.render_form(_form, function(rdata) {
                    if (callback) callback(rdata);
                });
                $(".placeholder").click(function() {
                    $(this).hide();
                    $('.webname' + bs).focus();
                })
                $('.path' + bs).val($("#defaultPath").text());
                $('.webname' + bs).focus(function() {
                    $(".placeholder").hide();
                });
                $('.webname' + bs).blur(function() {
                    if ($(this).val().length == 0) {
                        $(".placeholder").show();
                    }
                });
                $('.webname' + bs).focus(function(){
                    var _this = $(this),
                    tips = 'www will not add by default, if you need to access,please add it like:\
                    <br>hostname.com\
                    <br>www.hostname.com';
                    _this.attr('placeholder', '');
                    var loadT = layer.tips(tips, _this, {
                        tips: [1, '#20a53a'],
                        time: 0,
                        area: _this[0].clientWidth + 'px'
                    });
                    $(this).one('blur', function () {
                        layer.close(loadT);
                    });
                });
                $(".line").on("mouseenter", ".bt-ico-ask", function () {
                    var idd = $(this).attr('class').split(" ")[1], tip = $(this).attr('tip');
                    layer.tips(tip, '.' + idd + '', { tips: [1, '#d4d4d4'], time: 0, area: '300px'});
                });
                $(".line").on("mouseleave", ".bt-ico-ask", function () {
                    layer.closeAll('tips');
                });
                $(".domain_textarea").parents(".bt-form").css({'max-height': '565px','overflow': 'auto'});
            })
        })
    },
    get_all_phpversion: function(callback) {
        bt.send('GetPHPVersion', 'site/GetPHPVersion', {}, function(rdata) {
            if (callback) callback(rdata);
        })
    },
    get_site_phpversion: function(siteName, callback) {
        bt.send('GetSitePHPVersion', 'site/GetSitePHPVersion', { siteName: siteName }, function(rdata) {
            if (callback) callback(rdata);
        })
    },
    stop: function(id, name, callback) {
        bt.confirm({ title: lan.public_backup.stop_site + ' 【' + name + '】', msg: lan.site.site_stop_txt }, function(index) {
            if (index > 0) {
                var loadT = bt.load();
                bt.send('SiteStop', 'site/SiteStop', { id: id, name: name }, function(ret) {
                    loadT.close();
                    if(site && typeof callback == "undefined"){
						site.get_list();
					}else{
						if(callback) callback(ret);
					}
                    bt.msg(ret);
                });
            }
        });
    },
    start: function(id, name,callback) {
        bt.confirm({ title: lan.public_backup.start_site + ' 【' + name + '】', msg: lan.site.site_start_txt }, function(index) {
            if (index > 0) {
                var loadT = bt.load();
                bt.send('SiteStart', 'site/SiteStart', { id: id, name: name }, function(ret) {
                    loadT.close();
                    if(site && typeof callback == "undefined"){
						site.get_list();
					}else{
						if(callback) callback(ret);
					}
                    bt.msg(ret);
                });
            }
        });
    },
    backup_data: function(id, callback) {
        var loadT = bt.load(lan.database.backup_the);
        bt.send('ToBackup', 'site/ToBackup', { id: id }, function(rdata) {
            loadT.close();
            bt.msg(rdata);
            if (callback) callback(rdata);
        });
    },
    del_backup: function(id, siteId, siteName) {
        bt.confirm({ msg: lan.site.webback_del_confirm, title: lan.site.del_bak_file }, function(index) {
            var loadT = bt.load();
            bt.send('DelBackup', 'site/DelBackup', { id: id }, function(frdata) {
                loadT.close();
                if (frdata.status) {
                    if (site) site.site_detail(siteId, siteName);
                }
                bt.msg(frdata);
            });
        });
    },
    set_endtime: function(id, dates,callback) {
        var loadT = bt.load(lan.site.saving_txt);
        bt.send('SetEdate', 'site/SetEdate', { id: id, edate: dates }, function(rdata) {
            loadT.close();
            if(callback) callback(rdata);
        });
    },
    get_default_path: function(type, callback) {
        var vhref = '';
        if (bt.os == 'Linux') {
            switch (type) {
                case 0:
                    vhref = '/www/server/panel/data/defaultDoc.html';
                    break;
                case 1:
                    vhref = '/www/server/panel/data/404.html';
                    break;
                case 2:
                    var serverType = bt.get_cookie('serverType');
                    vhref = '/www/server/apache/htdocs/index.html';
                    if (serverType == 'nginx') vhref = '/www/server/nginx/html/index.html';
                    break;
                case 3:
                    vhref = '/www/server/stop/index.html';
                    break;
            }
        }
        if (callback) callback(vhref);
    },
    get_default_site: function(callback) {
        var loading = bt.load();
        bt.send('GetDefaultSite', 'site/GetDefaultSite', {}, function(rdata) {
            loading.close();
            if (callback) callback(rdata);
        })
    },
    set_default_site: function(name, callback) {
        var loading = bt.load();
        bt.send('SetDefaultSite', 'site/SetDefaultSite', { name: name }, function(rdata) {
            loading.close();
            if (callback) callback(rdata);
        })
    },
    get_dir_auth: function(id, callback) {
        var loading = bt.load();
        bt.send('get_dir_auth', 'site/get_dir_auth', { id: id }, function(rdata) {
            loading.close();
            if (callback) callback(rdata);
        })
    },
    get_php_deny: function(website, callback) {
        var loading = bt.load();
        bt.send('get_file_deny', 'config/get_file_deny', { website: website }, function(rdata) {
            loading.close();
            if (callback) callback(rdata);
        })
    },
    edit_php_deny: function(data, callback) {
        var loading = bt.load();
        bt.send('set_file_deny', 'config/set_file_deny', data, function(rdata) {
            loading.close();
            if (callback) callback(rdata);
        })
    },
    del_php_deny: function(data, callback) {
        var loading = bt.load();
        bt.send('del_file_deny', 'config/del_file_deny', data, function(rdata) {
            loading.close();
            if (callback) callback(rdata);
        })
    },
    create_dir_guard: function(data, callback) {
        var loading = bt.load();
        bt.send('set_dir_auth', 'site/set_dir_auth', { id: data.id, name: data.name, site_dir: data.site_dir, username: data.username, password: data.password }, function(rdata) {
            loading.close();
            if (callback) callback(rdata);
        })
    },
    edit_dir_account: function(data, callback) {
        var loading = bt.load();
        bt.send('modify_dir_auth_pass', 'site/modify_dir_auth_pass', { id: data.id, name: data.name, username: data.username, password: data.password }, function(rdata) {
            loading.close();
            if (callback) callback(rdata);
        })
    },
    delete_dir_guard: function(id, data, callback) {
        var loading = bt.load();
        bt.show_confirm(lan.public_backup.del + '[' + data + ']', lan.public_backup.del_dir, function() {
            bt.send('delete_dir_auth', 'site/delete_dir_auth', { id: id, name: data }, function(rdata) {
                loading.close();
                if (callback) callback(rdata);
            })
        })
    }
}



bt.form = {
    btn: {
        close: function(title, callback) {
            var obj = { title: lan.public_backup.turn_off, name: 'btn-danger' };
            if (title) obj.title = title;
            if (callback) obj['callback'] = callback;
            return obj;
        },
        submit: function(title, callback) {
            var obj = { title: lan.public_backup.submit, name: 'submit', css: 'btn-success' };
            if (title) obj.title = title;
            if (callback) obj['callback'] = callback;
            return obj;
        }
    },
    item: {
        data_access: {
            title: 'Permission',
            items: [{
                name: 'dataAccess',
                type: 'select',
                width: '100px',
                items: [
                    { title: lan.public_backup.local_server, value: '127.0.0.1' },
                    { title: lan.public_backup.every_one, value: '%' },
                    { title: lan.public_backup.specify_ip, value: 'ip' }
                ],
                callback: function(obj) {
                    var subid = obj.attr('name') + '_subid';
                    $('#' + subid).remove();
                    if (obj.val() == 'ip') {
                        obj.parent().append('<input id="' + subid + '" class="bt-input-text mr5" type="text" name="address" placeholder="' + lan.public_backup.access_ip_tips + '" style="width: 203px; display: inline-block;">');
                    }
                }
            }]
        },
        password: {
            title: lan.public_backup.pass,
            name: 'password',
            items: [
                { type: 'text', width: '311px', value: bt.get_random(16), event: { css: 'glyphicon-repeat', callback: function(obj) { bt.refresh_pwd(16, obj); } } }
            ]
        },
    }
}

bt.data = {
    database: {
				getType: function () {
					return bt.get_cookie('db_page_model') || 'mysql';
				},
        root: {
            title: lan.database.edit_pass_title,
            area: '530px',
            list: [{
                title: lan.public_backup.rootpass,
                name: 'password',
                items: [
                    { type: 'text', width: '311px', event: { css: 'glyphicon-repeat', callback: function(obj) { bt.refresh_pwd(16, obj); } } }
                ]
            }, ],
            btns: [
                bt.form.btn.close(),
                bt.form.btn.submit(lan.public_backup.submit, function(rdata, load) {
                    var loading = bt.load();
										var type = bt.data.database.getType();
										var params = { url: 'database?action=SetupPassword', data: rdata }
										if (type != 'mysql') {
											params.url = 'database/' + type + '/SetupPassword';
											params.data = { data: JSON.stringify(rdata) };
										}
                    bt_tools.send(params, function(rRet) {
											loading.close();
											bt.msg(rRet);
											if (rRet.status) load.close();
                    });
                })
            ]
        },
				mongo: {
					title: lan.database.edit_pass_title,
					area: '530px',
					list: [
						{
							title: lan.public_backup.rootpass,
							name: 'password',
							items: [
								{
									type: 'text',
									width: '311px',
									event: {
										css: 'glyphicon-repeat',
										callback: function (obj) {
											bt.refresh_pwd(16, obj);
										},
									},
								},
							],
						},
					],
					btns: [
						bt.form.btn.close(),
						bt.form.btn.submit(lan.public_backup.submit, function (rdata, load) {
							var loading = bt.load();
							var type = bt.data.database.getType();
							var url = 'database/' + type + '/set_auth_status';
							if (type == 'pgsql') url = 'database/' + type + '/set_root_pwd';
							bt_tools.send({ 
								url: url, 
								data: { data: JSON.stringify($.extend(rdata, { status: 1 })) }
							}, function (rRet) {
								loading.close();
								bt.msg(rRet);
								load.close();
							});
						}),
					],
				},
        data_add: {
            title: lan.database.add_title,
            area: '530px',
            list: [
                {
                    title: 'DBName',
                    items: [
                        {
                            name: 'name',
                            placeholder: lan.public_backup.new_db_name,
                            type: 'text',
                            width: '65%',
                            callback: function(obj) {
                                $('input[name="db_user"]').val(obj.val());
                            }
                        },
                        {
                            name: 'codeing',
                            type: 'select',
                            width: '27%',
                            items: [
                                { title: 'utf-8', value: 'utf8' },
                                { title: 'utf8mb4', value: 'utf8mb4' },
                                { title: 'gbk', value: 'gbk' },
                                { title: 'big5', value: 'big5' },
                            ]
                        }
                    ]
                },
                {
                    name: 'db_user',
                    title: lan.public_backup.user_name,
                    placeholder: lan.public_backup.db_user,
                    width: '65%'
                },
                bt.form.item.password,
                bt.form.item.data_access,
                {
                    title: lan.public_backup.add_to,
                    items: [
                        {
                            name: 'sid',
                            width: '65%',
                            type: 'select',
                            items: []
                        }
                    ]
                },
                {
                    html: '\
                        <div class="line" style="padding:0;">\
                            <span class="tname checkType">Force SSL</span>\
                            <div style="display: inline-block;">\
                                <input type="checkbox" name="active" id="check_ssl" class="btswitch btswitch-ios">\
                                <label for="check_ssl" class="btswitch-btn" style="margin-top: 5px;"></label>\
                            </div>\
                        </div>\
                    '
                }
            ],
            btns: [
                bt.form.btn.close(),
                bt.form.btn.submit(lan.public_backup.submit, function(rdata, load, callback) {
                    if (!rdata.address) rdata.address = rdata.dataAccess;
                    if (!rdata.ps) rdata.ps = rdata.name;
                    if (!rdata.ssl) rdata.ssl = $('#check_ssl').prop('checked')?'REQUIRE SSL':'';
                    var loading = bt.load();
										var type = bt.data.database.getType();
										var param = {
											url: 'database/' + type + '/AddDatabase',
											data: { data: JSON.stringify(rdata) }
										};
										if (type == 'mysql') {
											rdata['dtype'] = 'MySQL'
											param = { url: 'database?action=AddDatabase', data: rdata }
										}
                    bt_tools.send(param, function(rRet) {
											loading.close();
											if (rRet.status) load.close();
											if (callback) callback(rRet);
											bt.msg(rRet);
                    })
                })
            ],
            success: function () {
							$('[name=sid]').after('<a class="btlink" onclick="layer.closeAll();database.open_cloud_server()" style="margin-left: 10px;">' + lan.public.manage_cloud_server +  '</a>');
							var type = bt.data.database.getType();
							// 当前类型为mongodb
							if (type == 'mongodb') {
								// 是否开启安全认证，没开启隐藏用户名跟密码
								if (!mongodb.mongoDBAccessStatus) {
									$('.layui-layer.layui-layer-page .line').eq(1).hide();
									$('.layui-layer.layui-layer-page .line').eq(2).hide();
								}
								// 远程服务器类型判断
								$('[name=sid]').change(function () {
									// 为远程服务器时，默认开启安全认证
									if ($(this).val() != 0) {
										$('.layui-layer.layui-layer-page .line').eq(1).show();
										$('.layui-layer.layui-layer-page .line').eq(2).show();
									} else {
										if (!mongodb.mongoDBAccessStatuss) {
											$('.layui-layer.layui-layer-page .line').eq(1).hide();
											$('.layui-layer.layui-layer-page .line').eq(2).hide();
										}
									}
								})
							}
						}
        },
        data_access: {
            title: lan.public_backup.set_db_permissions,
            area: '480px',
            list: [
                { title: 'name', name: 'name', hide: true },
                bt.form.item.data_access,
                {
                    title: 'Force SSL',
                    items: [{
                        name: 'force_ssl',
                        type: 'switch',
                        value: 'false'
                    }],
                }
            ],
            btns: [
                bt.form.btn.close(),
                {
                    title: lan.public_backup.submit,
                    name: 'submit',
                    css: 'btn-success',
                    callback: function(rdata, load) {
                        var loading = bt.load();
                        rdata.access = rdata.dataAccess;
                        if (rdata.access == 'ip') rdata.access = rdata.address;
                        rdata.ssl = $("#force_ssl").prop('checked') ? 'REQUIRE SSL' : '';
                        bt.send('SetDatabaseAccess', 'database/SetDatabaseAccess', rdata, function(rRet) {
                            loading.close();
                            bt.msg(rRet);
                            if (rRet.status) load.close();
                        })
                    }
                }
            ]
        },
        data_pass: {
            title: lan.public_backup.change_db_pass,
            area: '530px',
            list: [
                { title: 'id', name: 'id', hide: true },
                { title: lan.public_backup.user_name, name: 'name', disabled: true },
                {
                    title: lan.public_backup.pass,
                    name: 'password',
                    items: [
                        { type: 'text', event: { css: 'glyphicon-repeat', callback: function(obj) { bt.refresh_pwd(16, obj); } } }
                    ]
                },
            ],
            btns: [
                { title: lan.public_backup.turn_off, name: 'close' },
                {
									title: lan.public_backup.submit,
									name: 'submit',
									css: 'btn-success',
									callback: function(rdata, load, callback) {
										var loading = bt.load();
										var type = bt.data.database.getType();
										var params = { url: 'database?action=ResDatabasePassword', data: rdata }
										if (type != 'mysql') {
											params.url = 'database/' + type + '/ResDatabasePassword';
											params.data = { data: JSON.stringify(rdata) };
										}
										bt_tools.send(params, function(rRet) {
												loading.close();
												bt.msg(rRet);
												if (rRet.status) load.close();
												if (callback) callback(rRet);
										})
									}
                }
            ]
        }
    },
    site: {
        add: {
            title: lan.site.site_add,
            area: '680px',
            list: [{
                    title: lan.public_backup.domain,
                    name: 'webname',
                    class:"domain_textarea",
                    items: [{
                        type: 'textarea',
                        width: '420px',
                        height:'80px',
                        style:'padding:10px;line-height: 15px;',
                        callback: function(obj) {
                            var array = obj.val().split("\n");
                            var ress = array[0].split(":")[0];
                            var res = bt.strim(ress.replace(new RegExp(/([-.])/g), '_'));
                            var ftp_user = res;
                            var data_user = res;
                            if (!isNaN(res.substr(0, 1))){
                                ftp_user = 'ftp_' + ftp_user;
                                data_user = 'sql_' + data_user;
                            }
                            if (data_user.length > 16) data_user = data_user.substr(0, 16)
                            obj.data('ftp', ftp_user);
                            obj.data('database', data_user);
                            $('.ftp_username').val(ftp_user);
                            $('.datauser').val(data_user);
                            var _form = obj.parents('div.bt-form');
                            var _path_obj = _form.find('input[name="path"]');
                            var path = _path_obj.val();
                            var defaultPath = $('#defaultPath').text();
                            var dPath = bt.rtrim(defaultPath, '/');
                            if (path.substr(0, dPath.length) == dPath) _path_obj.val(dPath + '/' + ress);
                            _form.find('input[name="ps"]').val(ress);
                            clearTimeout(bt.setTimeouts);
                            bt.setTimeouts =  setTimeout(function(){
                                if(bt.check_domain(ress)){
                                    if(ress.indexOf('www.') !== 0){
                                        $('.redirect_checkbox label').html('Add [<span>www.'+ ress +'</span>] domain name to the main domain name');
                                    }else if(ress.indexOf('www.') === 0){
                                        $('.redirect_checkbox label').html('Add <span>'+ ress.replace(/^www\./,'') +'</span> to the main domain');
                                    }
                                    $('.redirect_checkbox').show();
                                }else{
                                    $('.redirect_checkbox,redirect_tourl').hide();
                                }
                            },100);
                        },
                        placeholder: lan.public_backup.domian_tips
                    }]
                },{
                    title:'',
                    name:'redirect',
                    class:'redirect_checkbox',
                    hide:true,
                    items:[{
                        type:'checkbox',
                        text:'',
                        callback:function(obj){
                            var domain = $('.redirect_checkbox').find('span').text(),
                                domain_textarea = $('.domain_textarea textarea'),
                                domainList = domain_textarea.val().split('\n'),
                                domain_one = domainList[0].split(":")[0];
                            if(obj.redirect){
                                domain_textarea.val(domain_textarea.val() + '\r' + domain);
                                var line = $(bt.render_form_line({
                                    title:"Redirect",
                                    name:'tourl',
                                    class:'redirect_tourl',
                                    items:[{
                                        type:'radio_group',
                                        value:0,
                                        list:[
                                            {value:0,text:'No'},
                                            {value:1,text:'Redirect the main domain name [<span title="'+ domain_one +'"> '+ domain_one +'</span>] to [<span title="'+ domain +'">'+ domain +'</span>] domain name'},
                                            {value:2,text:'Redirect the [<span title="'+ domain +'">'+ domain +'</span>] domain name to the main domain [<span title="'+ domain_one +'">'+ domain_one +'</span>]'}
                                        ]
                                    }],
                                }).html);
                                $('.redirect_checkbox.line').after(line);
                            }else{
                                for(var i = domainList.length-1;i >= 0;i--){
                                    if(domainList[i] === domain) domainList.splice(i,1);
                                }
                                domain_textarea.val(domainList.join('\n'));
                                $('.redirect_checkbox').next('.redirect_tourl').remove();
                            }
                        }
                    }]
                },
                { title: lan.public_backup.ps, name: 'ps', placeholder: lan.public_backup.site_ps },
                {
                    title: lan.public_backup.root_dir,
                    name: 'path',
                    items: [
                        { type: 'text', width: '330px', event: { css: 'glyphicon-folder-open', callback: function(obj) { bt.select_path(obj); } } }
                    ]
                },
                {
                    title: 'FTP',
                    items: [{
                        name: 'ftp',
                        type: 'select',
                        items: [
                            { value: 'false', title: lan.public_backup.dont_create },
                            { value: 'true', title: lan.public_backup.create }
                        ],
                        callback: function(obj) {
                            var subid = obj.attr('name') + '_subid';
                            $('#' + subid).remove();
                            if (obj.val() == 'true') {
                                var _bs = obj.parents('div.bt-form').attr('data-id');
                                var ftp_user = $('textarea[name="webname"]').data('ftp');
                                var item = {
                                    title: lan.public_backup.set_ftp,
                                    class: 'pb0',
                                    name: 'ftp_tips',
                                    items: [
                                        { name: 'ftp_username', title: lan.public_backup.user_name, width: '160px', value: ftp_user },
                                        { name: 'ftp_password', title: lan.public_backup.pass, width: '160px', value: bt.get_random(16) }
                                    ],
                                    ps_help: lan.public_backup.ftp_tips
                                }
                                var _tr = bt.render_form_line(item)

                                obj.parents('div.line').append('<div class="line pb0" id=' + subid + '>' + _tr.html + '</div>');
                            }
                        }
                    }]
                },
                {
                    title: lan.public_backup.db,
                    items: [{
                            name: 'sql',
                            type: 'select',
                            items: [
                                { value: 'false', title: lan.public_backup.dont_create },
                                { value: 'MySQL', title: 'MySQL' },
                                { value: 'SQLServer', title: 'SQLServer' }
                            ],
                            callback: function(obj) {
                                var subid = obj.attr('name') + '_subid';
                                $('#' + subid).remove();
                                if (obj.val() != 'false') {
                                    if (bt.os == 'Linux' && obj.val() == 'SQLServer') {
                                        obj.val('false');
                                        bt.msg({ msg: lan.public_backup.unsupport_sqlserver, icon: 2 });
                                        return;
                                    }
                                    var _bs = obj.parents('div.bt-form').attr('data-id');
                                    var data_user = $('textarea[name="webname"]').data('database');
                                    var item = {
                                        title: lan.public_backup.db_set,
                                        class: 'pb0',
                                        name: 'sql_tips',
                                        items: [
                                            { name: 'datauser', title: lan.public_backup.user_name, width: '160px', value: data_user },
                                            { name: 'datapassword', title: lan.public_backup.pass, width: '160px', value: bt.get_random(16) }
                                        ],
                                        ps_help: lan.public_backup.create_site_tips
                                    }
                                    var _tr = bt.render_form_line(item)
                                    obj.parents('div.line').append('<div class="line pb0" id=' + subid + '>' + _tr.html + '</div>');
                                }
                            }
                        },
                        {
                            name: 'codeing',
                            type: 'select',
                            items: [
                                { value: 'utf8', title: 'utf-8' },
                                { value: 'utf8mb4', title: 'utf8mb4' },
                                { value: 'gbk', title: 'gbk' },
                                { value: 'big5', title: 'big5' }
                            ]
                        }
                    ]
                },
                {
                    title: 'Program type',
                    type: 'select',
                    name: 'type',
                    disabled: (bt.contains(bt.get_cookie('serverType'), 'IIS') ? false : true),
                    items: [
                        { value: 'PHP', title: 'PHP' },
                        { value: 'Asp', title: 'Asp' },
                        { value: 'Aspx', title: 'Aspx' },
                    ],
                    callback: function(obj) {
                        if (obj.val() == 'Asp' || obj.val() == 'Aspx') {
                            obj.parents('div.line').next().hide();
                        } else {
                            obj.parents('div.line').next().show();
                        }
                    }
                },
                {
                    title: lan.public_backup.php_v,
                    name: 'version',
                    type: 'select',
                    items: [
                        { value: '00', title: lan.public_backup.sitic }
                    ]
                }, {
                    title: lan.public_backup.site_classification,
                    name: 'type_id',
                    type: 'select',
                    width: 'auto',
                    items: [

                    ]
                }, {
                    title:'SSL',
                    class:'ssl_checkbox',
                    items:[{
                        type:'checkbox',
                        name:'set_ssl',
                        text:'Apply for SSL',
                        callback:function(obj){
                            if(!obj.set_ssl){
                                $('[name="force_ssl"]').prop('checked',false);
                            }
                        }
                    },{
                        type:'checkbox',
                        name:'force_ssl',
                        text:'HTTP redirect to HTTPS',
                        callback:function(obj){
                            if(obj.force_ssl){
                                $('[name="set_ssl"]').prop('checked',true);
                            }
                        }
                    },{
                        type:'html',
                        html:'<ul class="help-info-text c7" style="color:red;margin-top:0;"><li style="line-height: 17px;">If you need to apply for SSL, please make sure that the domain name has added A record resolution for the domain name</li></ul>'
                    }]
                }
            ],
            btns: [
                { title: lan.public_backup.turn_off, name: 'close' },
                {
                    title: lan.public_backup.submit,
                    name: 'submit',
                    css: 'btn-success',
                    callback: function(rdata, load, callback) {
                        var loading = bt.load();
                        if (!rdata.webname) {
                            bt.msg({ msg: lan.public_backup.domain_format_not_right, icon: 2 });
                            return;
                        }
                        var webname = bt.replace_all(rdata.webname, 'http:\\/\\/', '');
                        webname = bt.replace_all(webname, 'https:\\/\\/', '');
                        var arrs = webname.split('\n');
                        var list = [];
                        var domain_name, port;
                        for (var i = 0; i < arrs.length; i++) {
                            if (arrs[i]) {
                                var temp = arrs[i].split(':');
                                var item = {};
                                item['name'] = temp[0]
                                item['port'] = temp.length > 1 ? temp[1] : 80;
                                if (!bt.check_domain(item.name)) {
                                    bt.msg({ msg: lan.site.domain_err_txt, icon: 2 })
                                    return;
                                }
                                if (i > 0) {
                                    list.push(arrs[i]);
                                } else {
                                    domain_name = item.name;
                                    port = item.port;
                                }
                            }
                        }
                        var domain = {};
                        domain['domain'] = domain_name;
                        domain['domainlist'] = list;
                        domain['count'] = list.length;
                        rdata.webname = JSON.stringify(domain);
                        rdata.port = port;
                        rdata.tourl = parseInt($('[name="tourl"]:checked').val());
                        if(rdata.redirect){
                            if(rdata.tourl){
                                var domains =  $('#tourl_'+ rdata.tourl).next().find('span');
                                rdata.redirect = $(domains[0]).text();
                                rdata.tourl = $(domains[1]).text();
                            }else{
                                delete rdata.redirect;
                                delete rdata.tourl;
                            }
                        }else {
                            delete rdata.redirect;
                            delete rdata.tourl;
                        }
                        rdata.set_ssl = rdata.set_ssl?1:0
                        rdata.force_ssl = rdata.force_ssl?1:0
                        bt.send('AddSite', 'site/AddSite', rdata, function(rRet) {
                            loading.close();
                            if (rRet.siteStatus) load.close();
                            if (callback) callback(rRet);
                        })
                    }
                }
            ]
        }
    },
    ftp: {
        add: {
            title: lan.ftp.add_title,
            area: '530px',
            list: [{
                    title: lan.public_backup.user_name,
                    name: 'ftp_username',
                    callback: function(obj) {
                        var defaultPath = $('#defaultPath').text();
                        var wootPath = bt.rtrim(defaultPath, '/');
                        if (bt.contains($('input[name="path"]').val(), wootPath)) {
                            $('input[name="path"]').val(wootPath + '/' + obj.val())
                        }
                    }
                },
                {
                    title: lan.public_backup.pass,
                    name: 'ftp_password',
                    items: [
                        { type: 'text', width: '330px', value: bt.get_random(16), event: { css: 'glyphicon-repeat', callback: function(obj) { bt.refresh_pwd(16, obj); } } }
                    ]
                },
                {
                    title: lan.public_backup.root_dir,
                    name: 'path',
                    items: [
                        { type: 'text', event: { css: 'glyphicon-folder-open', callback: function(obj) { bt.select_path(obj); } } }
                    ]
                }
            ],
            btns: [
                { title: lan.public_backup.turn_off, name: 'close' },
                {
                    title: lan.public_backup.submit,
                    name: 'submit',
                    css: 'btn-success',
                    callback: function(rdata, load, callback) {
                        var loading = bt.load();
                        if (!rdata.ps) rdata.ps = rdata.ftp_username;
                        bt.send('AddUser', 'ftp/AddUser', rdata, function(rRet) {
                            loading.close();
                            if (rRet.status) load.close();
                            if (callback) callback(rRet);
                            bt.msg(rRet);
                        })
                    }
                }
            ]
        },
        set_port: {
            title: lan.ftp.port_title,
            skin: '',
            area: '500px',
            list: [
                { title: lan.public_backup.default_port, name: 'port', width: '250px' }
            ],
            btns: [
                { title: lan.public_backup.turn_off, name: 'close' },
                {
                    title: lan.public_backup.submit,
                    name: 'submit',
                    css: 'btn-success',
                    callback: function(rdata, load, callback) {
                        var loading = bt.load();
                        bt.send('setPort', 'ftp/setPort', rdata, function(rRet) {
                            loading.close();
                            if (rRet.status) load.close();
                            //if(callback) callback(rRet);
                            bt.msg(rRet);
                        })
                    }
                }
            ]
        },
        set_password: {
            title: lan.ftp.pass_title,
            area: '530px',
            list: [
                { title: 'id', name: 'id', hide: true },
                { title: lan.public_backup.user_name, name: 'ftp_username', disabled: true },
                {
                    title: lan.public_backup.pass,
                    name: 'new_password',
                    items: [
                        { type: 'text', event: { css: 'glyphicon-repeat', callback: function(obj) { bt.refresh_pwd(16, obj); } } }
                    ]
                },
            ],
            btns: [
                { title: lan.public_backup.turn_off, name: 'close' },
                {
                    title: lan.public_backup.submit,
                    name: 'submit',
                    css: 'btn-success',
                    callback: function(rdata, load, callback) {
                        bt.confirm({ msg: lan.ftp.pass_confirm, title: lan.ftp.stop_title }, function() {
                            var loading = bt.load();
                            bt.send('SetUserPassword', 'ftp/SetUserPassword', rdata, function(rRet) {
                                loading.close();
                                if (rRet.status) load.close();
                                if (callback) callback(rRet);
                                bt.msg(rRet);
                            })
                        })
                    }
                }
            ]
        }
    }
}
var form_group = {
	select_all:function(_arry){
		for(var j=0;j<_arry.length;j++){
			this.select(_arry[j]);
		}
	},
    select:function(elem){
        $(elem).after('<div class="bt_select_group"><div class="bt_select_active"><span class="select_val default">请选择</span><span class="glyphicon glyphicon-triangle-bottom" aria-hidden="true"></span> </div><ul class="bt_select_ul"></ul></div>');
		var _html = '',select_el = $(elem),select_group= select_el.next(),select_ul = select_group.find('.bt_select_ul'),select_val = select_group.find('.select_val'),select_icon = select_group.find('.glyphicon');
		select_el.find('option').each(function(index,el){
			var active = select_el.val() === $(el).val(),_val = $(el).val(),_name = $(el).text();
			_html += '<li data-val="'+ _val +'" class="'+ (active?'active':'') +'">'+ _name +'</li>';
			if(active){
				select_val.text(_name);
				_val !== ''?select_val.removeClass('default'):select_val.addClass('default');
			}
		});
		select_el.hide();
		select_ul.html(_html);
		$(elem).next('.bt_select_group').find('.bt_select_active').unbind('click').click(function(e){
			if(!$(this).next().hasClass('active')){
				$(this).parents().find('li').siblings().find('.bt_select_ul.active').each(function(){
					is_show_slect_parent(this);
				});
				$(this).parents('.rec-box').siblings().find('.bt_select_ul.active').each(function(){
					is_show_slect_parent(this);
				});
			}
			is_show_select_ul($(this).next().hasClass('active'));
			$(document).click(function(ev){
				is_show_select_ul(true);
				$(this).unbind('click');
				ev.stopPropagation();
				ev.preventDefault();
			});
			e.stopPropagation();
			e.preventDefault();
		});
		$(elem).next('.bt_select_group').find('.bt_select_ul li').unbind('click').click(function(){
			var _val = $(this).attr('data-val'),_name = $(this).text();
			$(this).addClass('active').siblings().removeClass('active');
			_val !== ''?select_val.removeClass('default'):select_val.addClass('default');
			select_val.text(_name);
			select_el.val(_val);
			$(elem).find('option[value="'+ _val +'"]').change();
			is_show_select_ul(true);
		});
		function is_show_slect_parent(that){
			$(that).removeClass('active fadeInUp animated');
			$(that).prev().find('.glyphicon').removeAttr('style');
			$(that).parent().removeAttr('style');
		}
		function is_show_select_ul(active){
			if(active){
				select_group.removeAttr('style');
				select_icon.css({'transform':'rotate(0deg)'});
				select_ul.removeClass('active fadeInUp animated');
			}else{
				select_group.css('borderColor','#20a53a');
				select_icon.css({'transform':'rotate(180deg)'});
				select_ul.addClass('active fadeInUp animated');
			}
		}
	},
	checkbox:function(){
		$('input[type="checkbox"]').each(function(index,el){
			$(el).hide();
			$(el).after('<div class="bt_checkbox_group '+ ($(this).prop("checked")?'active':'default') +'"></div>');
		});
		$('.bt_checkbox_group').click(function(){
			$(this).prev().click();
			if($(this).hasClass('active')){
				$(this).removeClass('active');
				$(this).prev().removeAttr('checked');
			}else{
				$(this).addClass('active');
				$(this).prev().attr('checked','checked');
			}
		});
	}
}

bt.public = {
    
    // 设置目录配额
    modify_path_quota:function (data,callback) {
      var loadT = bt.load(lan.public.modify_path_quota)
      $.post('/project/quota/modify_path_quota',data,function (res) {
        loadT.close()
        if(callback) callback(res)
      })
    },
  
    // 设置mysql配额
    modify_mysql_quota:function (data,callback) {
      var loadT = bt.load(lan.public.modify_mysql_quota)
      $.post('/project/quota/modify_mysql_quota',data,function (res) {
        loadT.close()
        if(callback) callback(res)
      })
    },
  
    /**
     * @description 获取quoto容量
    */
  
    get_quota_config:function (type) {
      return {
        fid: 'quota',
        title: lan.public.capacity,
        width: 120,
        template:function(row,index){
          var quota = row.quota;
          if(!quota.size) return '<a href="javascript:;" class="btlink">' + lan.public.notConfigured + '</a>'
          var size = quota.size * 1024 * 1024;
          var speed = ((quota.used / size) * 100).toFixed(2)
          var quotaFull = false
          if(quota.size > 0 && quota.used >= (size)) quotaFull = true;
          return '<div class=""><div class="progress mb0 cursor" style="height:12px;line-height:12px;vertical-align:middle;border-radius:2px;margin-top:3px;" title="' + lan.public.currentUsedCapacity + ': '+ (quotaFull?lan.public.finished:bt.format_size(quota.used)) +'\n' + lan.public.currentUsedCapacity + ': '+ bt.format_size(size) +'\n' + lan.public.modifyQuotaCapacity + '">'+
            '<div class="progress-bar progress-bar-'+ (speed >= 90?'danger':'success') +'" style="height:15px;line-height:15px;width: '+ speed +'%;display: inline-block;" role="progressbar" aria-valuemin="0" aria-valuemax="100"></div>'+
          '</div>'
        },
        event:function(row, index, ev){
          var quota = row.quota;
          var size = quota.size * 1024 * 1024
          var usedList = bt.format_size(quota.used).split(' ');
          var quotaFull = false
          if(quota.size > 0 && quota.used >= (size)) quotaFull = true;
          var types = {
              site: lan.site.website,
              ftp: lan.site.add_site.ftp,
              database: lan.site.database
          }
          layer.open({
            type:1,
            title: '[' + row.name + '] '+ types[type] + ' ' + lan.public.quotaCapacity,
            area:'476px',
            closeBtn:2,
            btn: [lan.public.save, lan.public.cancel],
            content:'<div class="bt-form pd20"><div class="line">'+
              '<span class="tname" style="width:180px">' + lan.public.currentUsedCapacity + '</span>'+
              '<div class="info-r">' +
                '<input type="text" name="used" disabled placeholder="" class="bt-input-text mr10 " style="width:120px;" value="'+ (!quotaFull?(quota.size != 0?usedList[0]:0):lan.public.capacityFinished) +'" /><span>'+ (!quotaFull?(quota.size != 0?usedList[1]:'MB'):'') +'</span>'+
              '</div>'+
                '<span class="tname" style="width:180px">' + lan.public.quotaCapacity + '</span>'+
                '<div class="info-r">'+
                  '<input type="text" name="quota_size" placeholder="" class="bt-input-text mr10 " style="width:120px;" value="'+ quota.size +'" /><span>MB</span>'+
                '</div>'+
              '</div>'+
              '<ul class="help-info-text c7">'+
                '<li style="color:red;">' + lan.public.capacityTips1 + '</li>'+
                '<li class="'+ (type == "database"?'hide':'') +'">' + lan.public.capacityTips2 + '</li>'+
                '<li class="'+ (type == "database"?'hide':'') +'">' + lan.public.capacityTips3 + '</li>'+
                '<li class="'+ (type == "database"?'':'hide') +'">' + lan.public.capacityTips4 + '</li>'+
                '<li>' + lan.public.capacityTips5 + '</li>'+
              '</ul>'+
            '</div>',
            yes:function (indexs) { 
              var quota_size = $('[name="quota_size"]').val()
              if(type === 'site' || type === 'ftp'){
                bt.public.modify_path_quota({data:JSON.stringify({size:quota_size,path:row.path})},function (res) {
                  if(res.status){
                    bt.msg(res)
                    layer.close(indexs)
                    setTimeout(function () { location.reload() },200)
                  }else{
                    layer.msg(res.msg,{ icon:res.status?1:2, area:'650px',time:0,shade:.3,closeBtn:2})
                  }
                })
              }else{
                bt.public.modify_mysql_quota({data:JSON.stringify({size:quota_size,db_name:row.name})},function (res) {
                  bt.msg(res)
                  if(res.status){
                    layer.close(indexs)
                    setTimeout(function () { location.reload() },200)
                  }
                })
              }
            }
          })
        }
      }
    }
}

//设置面板SSL
function setPanelSSL(){
	var loadT = layer.msg(lan.config.ssl_msg,{icon:16,time:0,shade: [0.3, '#000']});
    bt.send('get_cert_source', 'config/get_cert_source', {}, function (rdata) {
        layer.close(loadT);
        var sdata = rdata;
        var _data = {
            title: 'Panel SSL',
            area: '630px',
			class:'ssl_cert_from',
            list: [
              {
              		html:'<div><i class="layui-layer-ico layui-layer-ico3"></i><h3>'+lan.config.ssl_open_ps+'</h3><ul><li style="color:red;">'+lan.config.ssl_open_ps_1+'</li><li>'+lan.config.ssl_open_ps_2+'</li><li>'+lan.config.ssl_open_ps_3+'</li></ul></div>'
              },
                {
                    title: 'Cert Type',
                    name: 'cert_type',
                    type: 'select',
                    width: '200px',
                    value: sdata.cert_type,
                    items: [{value: '1', title: 'Self-signed certificate'}, {value: '2', title: 'Let\'s Encrypt'}],
                    callback: function (obj) {
                        var subid = obj.attr('name') + '_subid';
                        $('#' + subid).remove();
                        if (obj.val() == '2') {
                            var _tr = bt.render_form_line({
                                title: 'Admin E-Mail',
                                name: 'email',
								width: '320px',
                                placeholder: 'Admin E-Mail',
                                value: sdata.email
                            });
                            obj.parents('div.line').append('<div class="line" id=' + subid + '>' + _tr.html + '</div>');
                        }
                    }
                },
              {
                  html: '<div class="details"><input type="checkbox" id="checkSSL" /><label style="font-weight: 400;margin: -1px 5px 0px;" for="checkSSL">' + lan.config.ssl_open_ps_4 + '</label><a target="_blank" class="btlink" href="https://www.aapanel.com/forum/d/167-common-problems-after-opening-the-panel-certificate">' + lan.config.ssl_open_ps_5 + '</a></p></div>'
              }

            ],
            btns: [
                {
                    title: 'Close', name: 'close', callback: function (rdata, load, callback) {
                        load.close();
                        $("#panelSSL").prop("checked", false);
                    }
                },
                {
                    title: 'Submit', name: 'submit', css: 'btn-success', callback: function (rdata, load, callback) {
                      	if(!$('#checkSSL').is(':checked')){
                        	bt.msg({status:false,msg:'Please confirm the risk first!'})
                          	return;
                        }
                    	var confirm = layer.confirm('Whether to open the panel SSL certificate', {title:'Tips',btn: ['Confirm','Cancel'],icon:0,closeBtn:2}, function() {
                        var loading = bt.load();
                        bt.send('SetPanelSSL', 'config/SetPanelSSL', rdata, function (rdata) {
                            loading.close()
                            if (rdata.status) {
                            	layer.msg(rdata.msg,{icon:1});
                                $.get('/system?action=ReWeb', function () {
                                });
                                setTimeout(function () {
                                    window.location.href = ((window.location.protocol.indexOf('https') != -1) ? 'http://' : 'https://') + window.location.host + window.location.pathname;
                                }, 1500);
                            }
                            else {
                                layer.msg(rdata.msg,{icon:2});
                            }
                        })
						});
                    }

                }
            ],
            end: function () {
               
            }
        };

        var _bs = bt.render_form(_data);
        // setTimeout(function () {
        //     $('.cert_type' + _bs).trigger('change')
        // }, 200);
    });
}

var dynamic = {
	loadList: [],
	fileFunList: {},
	load: false,
	callback: null,

	// 初始化执行
	execution: function () {
		for (var i = 0; i < this.loadList.length; i++) {
			var fileName = this.loadList[i];
			if (fileName in this.fileFunList) this.fileFunList[fileName]();
		}
	},

	/**
	 * @description 动态加载js,css文件
	 * @param urls {string|array} 文件路径或文件数组
	 * @param fn {function|undefined} 回调函数
	 */
	require: function (urls, fn) {
		if (!Array.isArray(urls)) urls = [urls];

		this.fileFunList = {};

		var i = 0;
		var that = this;
		var total = urls.length;
		var callback = function () {
			i++;
			if (i < total) {
				that.loadFile(urls[i], callback);
			} else {
				fn && fn();
			}
		};
		this.loadFile(urls[i], callback);
	},
	/**
	 * @description 加载js,css文件
	 * @param {string} url 文件路径
	 * @param {function} fn 回调函数
	 */
	loadFile: function (url, fn) {
		this.load = true;

		var that = this;
		var element = this.createElement(url);

		if (element.readyState) {
			element.onreadystatechange = function (ev) {
				if (element.readyState === 'loaded' || element.readyState === 'complete') {
					element.onreadystatechange = null;
					that.execution();
					fn && fn.call(that);
					that.load = false;
				}
			};
		} else {
			element.onload = function (ev) {
				that.execution();
				fn && fn.call(that);
				that.load = false;
			};
		}
		document.getElementsByTagName('head')[0].appendChild(element);
	},
	/**
	 * @description 创建元素
	 * @param {string} url 文件路径
	 * @returns
	 */
	createElement: function (url) {
		var element = null;
		if (url.indexOf('.js') > -1) {
			element = document.createElement('script');
			element.type = 'text/javascript';
			element.src = bt.url_merge('/vue/' + url);
		} else if (url.indexOf('.css') > -1) {
			element = document.createElement('link');
			element.rel = 'stylesheet';
			element.href = bt.url_merge('/vue/' + url);
		}
		return element;
	},
	/**
	 * @default 执行延迟文件内容执行
	 * @param fileName {string} 文件名称，不要加文件后缀
	 * @param callback {function} 回调行数
	 */
	delay: function delay(fileName, callback) {
		if (!this.load) {
			callback();
			return false;
		}
		this.fileFunList[fileName] = callback;
	},
};

// 过滤编码
bt.htmlEncode = {
	/**
	 * @description 正则转换特殊字符
	 * @param {string} layid 字符内容
	 */
	htmlEncodeByRegExp: function (str) {
		if (typeof str == 'undefined' || str.length == 0) return '';
		return str
			.replace(/&/g, '&amp;')
			.replace(/</g, '&lt;')
			.replace(/>/g, '&gt;')
			.replace(/ /g, '&nbsp;')
			.replace(/\'/g, '&#39;')
			.replace(/\"/g, '&quot;')
			.replace(/\(/g, '&#40;')
			.replace(/\)/g, '&#41;')
			.replace(/`/g, '&#96;')
			.replace(/=/g, '＝');
	},
};