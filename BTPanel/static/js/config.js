function modify_port_val(port){
	layer.open({
		type: 1,
		area: '400px',
		title: 'Change Panel Port',
		closeBtn:2,
		shadeClose: false,
		btn:['Confirm','Cancel'],
		content: '<div class="bt-form pd20 pd70" style="padding:20px 35px;">\
				<ul style="margin-bottom:10px;color:red;width: 100%;background: #f7f7f7;padding: 10px;border-radius: 5px;font-size: 12px;">\
					<li style="color:red;font-size:13px;">1. Have a security group server, please release the new port in the security group in advance.</li>\
					<li style="color:red;font-size:13px;">2. If the panel is inaccessible after modifying the port, change the original port to the SSH command line by using the bt command.</li>\
				</ul>\
				<div class="line">\
	                <span class="tname" style="width: 70px;">Port</span>\
	                <div class="info-r" style="margin-left:70px">\
	                    <input name="portss" class="bt-input-text mr5" type="text" style="width:200px" value="'+ port +'">\
	                </div>\
                </div>\
                <div class="details" style="margin-top:5px;padding-left: 3px;">\
					<input type="checkbox" id="check_port">\
					<label style="font-weight: 400;margin: 3px 5px 0px;" for="check_port">I already understand</label>,<a target="_blank" class="btlink" href="https://forum.aapanel.com/d/599-how-to-release-the-aapanel-port">How to release the port?</a>\
				</div>\
			</div>',
		yes:function(index,layero){
			var check_port = $('#check_port').prop('checked'),_tips = '';
			if(!check_port){
				_tips = layer.tips('Please tick the one I already know', '#check_port', {tips:[1,'#ff0000'],time:5000});
				return false;
			}
			layer.close(_tips);
			$('#banport').val($('[name="portss"]').val());
			var _data = $("#set-Config").serializeObject();
			_data['port'] = $('[name="portss"]').val();
			var loadT = layer.msg(lan.config.config_save,{icon:16,time:0,shade: [0.3, '#000']});
			$.post('/config?action=setPanel',_data,function(rdata){
				layer.close(loadT);
				layer.msg(rdata.msg,{icon:rdata.status?1:2});
				if(rdata.status){
					layer.close(index);
					setTimeout(function(){
						window.location.href = ((window.location.protocol.indexOf('https') != -1)?'https://':'http://') + rdata.host + window.location.pathname;
					},4000);
				}
			});
		},
		success:function(){
			$('#check_port').click(function(){
				layer.closeAll('tips');
			});
		}
	});
}
$.fn.serializeObject = function(){
   var o = {};
   var a = this.serializeArray();
   $.each(a, function() {
       if (o[this.name]) {
           if (!o[this.name].push) {
               o[this.name] = [o[this.name]];
           }
           o[this.name].push(this.value || '');
       } else {
           o[this.name] = this.value || '';
       }
   });
   return o;
};


//关闭面板
function ClosePanel(){
	layer.confirm(lan.config.close_panel_msg,{title:lan.config.close_panel_title,closeBtn:2,icon:13,cancel:function(){
		$("#closePl").prop("checked",false);
	}}, function() {
		$.post('/config?action=ClosePanel','',function(rdata){
			layer.msg(rdata.msg,{icon:rdata.status?1:2});
			setTimeout(function(){window.location.reload();},1000);
		});
	},function(){
		$("#closePl").prop("checked",false);
	});
}

//设置自动更新
function SetPanelAutoUpload(){
	loadT = layer.msg(lan.public.config,{icon:16,time:0});
	$.post('/config?action=AutoUpdatePanel','',function(rdata){
		layer.close(loadT);
		layer.msg(rdata.msg,{icon:rdata.status?1:2});
	});
}




$('#panel_verification').click(function(){
	var _checked = $(this).prop('checked');
	if(_checked){
		layer.open({
			type: 1,
			area: ['600px','420px'],
			title: 'Google authentication binding',
			closeBtn: 2,
			shift: 5,
			shadeClose: false,
			content: '<div class="bt-form pd20 pd70 ssl_cert_from google_verify" style="padding:20px 35px;">\
				<div class="">\
					<i class="layui-layer-ico layui-layer-ico3"></i>\
					<h3>Warning! Do not understand this feature, do not open!</h3>\
					<ul style="width:91%;margin-bottom:10px;margin-top:10px;">\
						<li style="color:red;">You must use and understand this feature to decide if you want to open it!</li>\
						<li style="color:red;">If it is not possible to verify, enter "bt 24" on the command line to cancel Google authentication.</li>\
						<li>Once the service is turned on, bind it immediately to avoid the panel being inaccessible.</li>\
						<li>After opening, the panel will not be accessible. You can click the link below to find out the solution.</li>\
					</ul>\
				</div>\
				<div class="details" style="width: 90%;margin-bottom:10px;">\
					<input type="checkbox" id="check_verification">\
					<label style="font-weight: 400;margin: 3px 5px 0px;" for="check_verification">I already know the details and are willing to take risks</label>\
					<a target="_blank" class="btlink" href="https://forum.aapanel.com/d/357-how-to-use-google-authenticator-in-the-aapanel">Learn more</a>\
				</div>\
				<div class="bt-form-submit-btn">\
					<button type="button" class="btn btn-sm btn-danger close_verify">Close</button>\
					<button type="button" class="btn btn-sm btn-success submit_verify">Confirm</button>\
				</div>\
			</div>',
			success:function(layers,index){
				$('.submit_verify').click(function(e){
					var check_verification = $('#check_verification').prop('checked');
					if(!check_verification){
						layer.msg('Please check the consent risk first.',{icon:0});
						return false;
					}
					var loadT = layer.msg('Opening Google authentication, please wait...', { icon: 16, time: 0, shade: [0.3, '#000'] });
					set_two_step_auth({act:_checked},function(rdata){
						layer.close(loadT);
						if (rdata.status) layer.closeAll();
						layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
						if(rdata.status && _checked){
							$('.open_two_verify_view').click();
						}
					});
				});
				$('.close_verify').click(function(){
					layer.closeAll();
					$('#panel_verification').prop('checked',!_checked);
				});
			},cancel:function () {
				layer.closeAll();
				$('#panel_verification').prop('checked',!_checked);
			}
		});
	}else{
		bt.confirm({
			title: 'Google authentication',
			msg: 'Turn off Google authentication, do you want to continue?',
			cancel: function () {
				$('#panel_verification').prop('checked',!_checked);
			}}, function () {
				var loadT = layer.msg('Google authentication is being turned off, please wait...', { icon: 16, time: 0, shade: [0.3, '#000'] });
				set_two_step_auth({act:_checked},function(rdata){
					layer.close(loadT);
					if (rdata.status) layer.closeAll();
					layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
					if(rdata.status && _checked){
						$('.open_two_verify_view').click();
					}
				});
			},function () {
				$('#panel_verification').prop('checked',!_checked);
		   });
	}

	// console.log(_data);

});

$('.open_two_verify_view').click(function(){
	var _checked = $('#panel_verification').prop('checked');
	if(!_checked){
		layer.msg('Please turn on Google authentication first.',{icon:0});
		return false;
	}
	layer.open({
        type: 1,
        area: ['600px','670px'],
        title: 'Google authentication binding',
        closeBtn: 2,
        shift: 5,
        shadeClose: false,
        content: '<div class="bt-form pd20" style="padding:20px 35px;">\
					<div class="verify_title">Login authentication based on Google Authenticator</div>\
					<div class="verify_item">\
						<div class="verify_vice_title">1. Key binding</div>\
						<div class="verify_conter">\
							<div class="verify_box">\
								<div class="verify_box_line">Account：<span class="username"></sapn></div>\
								<div class="verify_box_line">Key：<span class="userkey"></sapn></div>\
								<div class="verify_box_line">Type：<span class="usertype">Time based</sapn></div>\
							</div>\
						</div>\
					</div>\
					<div class="verify_item">\
						<div class="verify_vice_title">2. Scan code binding (Using Google Authenticator APP scan)</div>\
						<div class="verify_conter" style="text-align:center;padding-top:10px;">\
							<div id="verify_qrcode"></div>\
						</div>\
					</div>\
					<div class="verify_tips">\
						<p>Tips: Please use the "Google Authenticator APP" binding to support Android, IOS system.<a href="https://forum.aapanel.com/d/357-how-to-use-google-authenticator-in-the-aapanel" class="btlink" target="_blank">Use tutorial</a></p>\
						<p style="color:red;">Once you have turned on the service, use the Google Authenticator app binding now to avoid having to sign in.</p>\
					</div>\
				</div>',
		success:function(e){
			get_two_verify(function(res){
				$('.verify_box_line .username').html(res.username);
				$('.verify_box_line .userkey').html(res.key);
			});
			get_qrcode_data(function(res){
				jQuery('#verify_qrcode').qrcode({
					render: "canvas",
					text: res,
					height:150,
					width:150
				});
			});
		}
    });
});
var three_channel_status = {};
(function(){
	check_two_step(function(res){
		$('#panel_verification').prop('checked',res.status);
	});
	get_three_channel(function(res){
		three_channel_status = res;
		$('#channel_auth').val(!res.user_mail.user_name && !res.dingding.dingding ? 'Email is not set':(res.user_mail.user_name? 'Email is set':(res.dingding.dingding? 'dingding is set': '')))
	});
	get_login_send(function(rdata){
		$('#panel_report').val(!rdata.status ? 'Email is not set':(rdata.msg.mail? 'Already set':'Not set'))
	})
})()

function get_three_channel(callback){
	$.post('/config?action=get_settings',function(res){
		if(callback) callback(res);
	});
}
function get_login_send(callback){
    var loadS = bt.load('Getting login information, please wait...')
    $.post('/config?action=get_login_send',function(res){
        loadS.close()
		if(callback) callback(res);
	});
}
function login_ipwhite(obj,callback){
    var loadY = bt.load('Getting IP lists, please wait...')
    $.post('/config?action=login_ipwhite',obj,function(res){
        loadY.close()
		if(!res.status) return layer.msg(res.msg,{icon:res.status?1:2})
		if(callback) callback(res);
	});
}

function check_two_step(callback){
	$.post('/config?action=check_two_step',function(res){
		if(callback) callback(res);
	});
}
function get_qrcode_data(callback){
	$.post('/config?action=get_qrcode_data',function(res){
		if(callback) callback(res);
	});
}
function get_two_verify(callback){
	$.post('/config?action=get_key',function(res){
		if(callback) callback(res);
	});
}
function set_two_step_auth(obj,callback){
	$.post('/config?action=set_two_step_auth',{act:obj.act?1:0},function(res){
		if(callback) callback(res);
	});
}

$(".set-submit").click(function(){
	var data = $("#set-Config").serialize();
	layer.msg(lan.config.config_save,{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/config?action=setPanel',data,function(rdata){
		layer.closeAll();
		layer.msg(rdata.msg,{icon:rdata.status?1:2});
		if(rdata.status){
			setTimeout(function(){
				window.location.href = ((window.location.protocol.indexOf('https') != -1)?'https://':'http://') + rdata.host + window.location.pathname;
			},1500);
		}
	});

});


function modify_auth_path() {
    var auth_path = $("#admin_path").val();
    btn = "<button type='button' class='btn btn-success btn-sm' onclick=\"bindBTName(1,'b')\">"+lan.config.confirm+"</button>";
    layer.open({
        type: 1,
        area: "500px",
        title: lan.config.change_safe_entry,
        closeBtn: 2,
        shift: 5,
        shadeClose: false,
        content: '<div class="bt-form bt-form pd20 pb70">\
                    <div class="line ">\
                        <span class="tname">'+lan.config.entry_addr+'</span>\
                        <div class="info-r">\
                            <input name="auth_path_set" class="bt-input-text mr5" type="text" style="width: 311px" value="'+ auth_path+'">\
                        </div></div>\
                        <div class="bt-form-submit-btn">\
                            <button type="button" class= "btn btn-sm btn-danger" onclick="layer.closeAll()"> '+lan.config.turn_off+'</button>\
                            <button type="button" class="btn btn-sm btn-success" onclick="set_auth_path()">'+lan.config.submit+'</button>\
                    </div></div>'
    })





}

function set_auth_path() {
    var auth_path = $("input[name='auth_path_set']").val();
    var loadT = layer.msg(lan.config.config_save, { icon: 16, time: 0, shade: [0.3, '#000'] });
    $.post('/config?action=set_admin_path', { admin_path: auth_path }, function (rdata) {
        layer.close(loadT);
        if (rdata.status) {
            layer.closeAll();
            $("#admin_path").val(auth_path);
        }

        setTimeout(function () { layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 }); }, 200);
    });
}


function syncDate() {

	var loadT = layer.msg(lan.config.config_sync,{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/config?action=syncDate','',function(rdata){
		layer.close(loadT);
		layer.msg(rdata.msg,{icon:1});
		setTimeout(function(){
				window.location.reload();
			},1500);
	});
}

//PHP守护程序
function Set502(){
	var loadT = layer.msg(lan.public.the,{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/config?action=Set502','',function(rdata){
		layer.close(loadT);
		layer.msg(rdata.msg,{icon:rdata.status?1:2});
	});
}

//绑定修改宝塔账号
function bindBTName(a,type){
	var titleName = lan.config.config_user_binding;
	if(type == "b"){
		btn = "<button type='button' class='btn btn-success btn-sm' onclick=\"bindBTName(1,'b')\">"+lan.config.binding+"</button>";
	}
	else{
		titleName = lan.config.config_user_edit;
		btn = "<button type='button' class='btn btn-success btn-sm' onclick=\"bindBTName(1,'c')\">"+lan.public.edit+"</button>";
	}
	if(a == 1) {
		p1 = $("#p1").val();
		p2 = $("#p2").val();
		var loadT = layer.msg(lan.config.token_get,{icon:16,time:0,shade: [0.3, '#000']});
		$.post(" /ssl?action=GetToken", "username=" + p1 + "&password=" + p2, function(b){
      bt.clear_cookie('bt_user_info')
			layer.close(loadT);
			layer.msg(b.msg, {icon: b.status?1:2});
			if(b.status) {
				window.location.reload();
				$("input[name='btusername']").val(p1);
			}
		});
		return
	}
	layer.open({
		type: 1,
		area: "290px",
		title: titleName,
		closeBtn: 2,
		shift: 5,
		shadeClose: false,
		content: "<div class='bt-form pd20 pb70'><div class='line'><span class='tname' style='width:100px;'>"+lan.public.user+"</span><div class='info-r' style='margin-left:100px;'><input class='bt-input-text' type='text' name='username' id='p1' value='' placeholder='"+lan.config.user_bt+"' style='width:100%'/></div></div><div class='line'><span class='tname' style='width:100px;'>"+lan.public.pass+"</span><div class='info-r' style='margin-left:100px;'><input class='bt-input-text' type='password' name='password' id='p2' value='' placeholder='"+lan.config.pass_bt+"' style='width:100%'/></div></div><div class='bt-form-submit-btn'><button type='button' class='btn btn-danger btn-sm' onclick=\"layer.closeAll()\">"+lan.public.cancel+"</button> "+btn+"</div></div>"
	})
}
//解除绑定宝塔账号
function UnboundBt(){
	var name = $("input[name='btusername']").val();
	layer.confirm(lan.config.binding_un_msg,{closeBtn:2,icon:3,title:lan.config.binding_un},function(){
		$.get("/ssl?action=DelToken",function(b){
			layer.msg(b.msg,{icon:b.status? 1:2})
      bt.clear_cookie('bt_user_info')
			if(b.status){
			    window.location.reload();
			    $("input[name='btusername']").val('');
			}
		})
	})
}

//设置API
function apiSetup(){
	var loadT = layer.msg(lan.config.token_get,{icon:16,time:0,shade: [0.3, '#000']});
	$.get('/api?action=GetToken',function(rdata){
		layer.close(loadT);

	});
}


//设置模板
function setTemplate(){
	var template = $("select[name='template']").val();
	var loadT = layer.msg(lan.public.the,{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/config?action=SetTemplates','templates='+template,function(rdata){
		layer.close(loadT);
		layer.msg(rdata.msg,{icon:rdata.status?1:5});
		if(rdata.status === true){
			$.get('/system?action=ReWeb',function(){});
			setTimeout(function(){
				window.location.reload();
			},3000);
		}
	});
}

//设置面板SSL
function setPanelSSL(){
	var status = $("#panelSSL").prop("checked");
	var loadT = layer.msg(lan.config.ssl_msg,{icon:16,time:0,shade: [0.3, '#000']});
	if(status){
		var confirm = layer.confirm('Whether to close the panel SSL certificate', {title:'Tips',btn: ['Confirm','Cancel'],icon:0,closeBtn:2}, function() {
            bt.send('SetPanelSSL', 'config/SetPanelSSL', {}, function (rdata) {
                layer.close(loadT);
                if (rdata.status) {
                	layer.msg(rdata.msg,{icon:1});
                    $.get('/system?action=ReWeb', function () {
                    });
                    setTimeout(function () {
                        window.location.href = ((window.location.protocol.indexOf('https') != -1) ? 'http://' : 'https://') + window.location.host + window.location.pathname;
                    }, 1500);
                }
                else {
                    layer.msg(res.rdata,{icon:2});
                }
            });
            return;
        })
	}
	else {
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
                  	html:'<div class="details"><input type="checkbox" id="checkSSL" /><label style="font-weight: 400;margin: 3px 5px 0px;" for="checkSSL">'+lan.config.ssl_open_ps_4+'</label><a target="_blank" class="btlink" href="https://forum.aapanel.com/d/167-common-problems-after-opening-the-panel-certificate">'+lan.config.ssl_open_ps_5+'</a></p></div>'
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
                    $("#panelSSL").prop("checked", false);
                }
            };

            var _bs = bt.render_form(_data);
            setTimeout(function () {
                $('.cert_type' + _bs).trigger('change')
            }, 200);
        });
    }
}

function GetPanelSSL(){
	var loadT = layer.msg(lan.config.get_cert,{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/config?action=GetPanelSSL',{},function(cert){
		layer.close(loadT);
		var certBody = '<div class="tab-con">\
			<div class="myKeyCon ptb15">\
				<div class="ssl-con-key pull-left mr20">'+lan.config.key+'<br>\
					<textarea id="key" class="bt-input-text">'+cert.privateKey+'</textarea>\
				</div>\
				<div class="ssl-con-key pull-left">'+lan.config.pem_cert+'<br>\
					<textarea id="csr" class="bt-input-text">'+cert.certPem+'</textarea>\
				</div>\
				<div class="ssl-btn pull-left mtb15" style="width:100%">\
					<button class="btn btn-success btn-sm" onclick="SavePanelSSL()">'+lan.config.save+'</button>\
				</div>\
			</div>\
			<ul class="help-info-text c7 pull-left">\
				<li>'+lan.config.ps+'<a href="http://www.bt.cn/bbs/thread-704-1-1.html" class="btlink" target="_blank">['+lan.config.help+']</a>。</li>\
				<li>'+lan.config.ps1+'</li><li>'+lan.config.ps2+'</li>\
			</ul>\
		</div>'
		layer.open({
			type: 1,
			area: "600px",
			title: lan.config.custom_panel_cert,
			closeBtn: 2,
			shift: 5,
			shadeClose: false,
			content:certBody
		});
	});
}

function SavePanelSSL(){
	var data = {
		privateKey:$("#key").val(),
		certPem:$("#csr").val()
	}
	var loadT = layer.msg(lan.config.ssl_msg,{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/config?action=SavePanelSSL',data,function(rdata){
		layer.close(loadT);
		if(rdata.status){
			layer.closeAll();
		}
		layer.msg(rdata.msg,{icon:rdata.status?1:2});
	});
}

function SetDebug() {
    var status_s = {false:'open',true:'close'}
    var debug_stat = $("#panelDebug").prop('checked');
    bt.confirm({
		title: (debug_stat?'Open':'Close') + " developer mode",
		msg: "Do you confirm to "+ (debug_stat?'open':'close') +" developer mode?",
		cancel: function () {
			$("#panelDebug").prop('checked',debug_stat);
    	}}, function () {
			var loadT = layer.msg(lan.public.the, { icon: 16, time: 0, shade: [0.3, '#000'] });
			$.post('/config?action=set_debug', {}, function (rdata) {
				layer.close(loadT);
				if (rdata.status) layer.closeAll()
				layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
			});
		},function () {
		$("#panelDebug").prop('checked',debug_stat);
	});
}

function set_local() {
    var status_s = { false: 'Open', true: 'Close' }
    var debug_stat = $("#panelLocal").prop('checked');
    bt.confirm({
		title: status_s[debug_stat] + "Offline mode",
		msg: "Do you really want "+ status_s[debug_stat] + "offline mode?",
	    cancel: function () {
			$("#panelLocal").prop('checked',debug_stat);
    	}}, function () {
        	var loadT = layer.msg(lan.public.the, { icon: 16, time: 0, shade: [0.3, '#000'] });
			$.post('/config?action=set_local', {}, function (rdata) {
				layer.close(loadT);
				if (rdata.status) layer.closeAll();
				layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
			});
        },function () {
		$("#panelLocal").prop('checked',debug_stat);
    });
}

if(window.location.protocol.indexOf('https') != -1){
	$("#panelSSL").prop('checked',true);
}

var weChat = {
		settiming:'',
		relHeight:500,
		relWidth:500,
		userLength:'',
		init:function(){
			var _this = this;
			$('.layui-layer-page').css('display', 'none');
			$('.layui-layer-page').width(_this.relWidth);
			$('.layui-layer-page').height(_this.relHeight);
			$('.bt-w-menu').height((_this.relWidth - 1) - $('.layui-layer-title').height());
			var width = $(document).width();
			var height = $(document).height();
			var boxwidth =  (width / 2) - (_this.relWidth / 2);
			var boxheight =  (height / 2) - (_this.relHeight / 2);
			$('.layui-layer-page').css({
				'left':boxwidth +'px',
				'top':boxheight+'px'
			});
			$('.boxConter,.layui-layer-page').css('display', 'block');
			$('.layui-layer-close').click(function(event) {
				window.clearInterval(_this.settiming);
			});
			this.getUserDetails();
			$('.iconCode').hide();
			$('.personalDetails').show();
		},
		// 获取二维码
		getQRCode:function(){
			var _this = this;
			var qrLoading = layer.msg(lan.config.get_qr_core,{time:0,shade: [0.4,'#fff'],icon:16});
			$.get('/wxapp?action=blind_qrcode', function(res) {
				layer.close(qrLoading);
				if (res.status){
                	$('#QRcode').empty();
					$('#QRcode').qrcode({
					    render: "canvas", //也可以替换为table
					    width: 200,
					    height: 200,
					    text:res.msg
					});
					// $('.QRcode img').attr('src', res.msg);
					_this.settiming =  setInterval(function(){
						_this.verifyBdinding();
					},2000);
				}else{
					layer.msg(lan.config.get_qr_core_fail,{icon:2});
				}
			});
		},
		// 获取用户信息
		getUserDetails:function(type){
			var _this = this;
			var conter = '';
			$.get('/wxapp?action=get_user_info',function(res){
				clearInterval(_this.settiming);
				if (!res.status){
					layer.msg(res.msg,{icon:2,time:3000});
					$('.iconCode').hide();
					return false;
				}
				if (JSON.stringify(res.msg) =='{}'){
					if (type){
						layer.msg(lan.config.qrcode_no_list,{icon:2});
					}else{
						_this.getQRCode();
					}
					$('.iconCode').show();
					$('.personalDetails').hide();
					return false;
				}
				$('.iconCode').hide();
				$('.personalDetails').show();
				var datas = res.msg;
				for(var item in datas){
					conter += '<li class="item">\
								<div class="head_img"><img src="'+datas[item].avatarUrl+'" title="'+lan.config.user_img+'" /></div>\
								<div class="nick_name"><span>'+lan.config.nikename+':</span><span class="nick"></span>'+datas[item].nickName+'</div>\
								<div class="cancelBind">\
									<a href="javascript:;" class="btlink" title="'+lan.config.unbind_wechat+'" onclick="weChat.cancelBdinding('+ item +')">'+lan.config.unbind+'</a>\
								</div>\
							</li>'
				}
				conter += '<li class="item addweChat" style="height:45px;"><a href="javascript:;" class="btlink" onclick="weChat.addweChatView()"><span class="glyphicon glyphicon-plus"></span>'+lan.config.add_bind_account+'</a></li>'
				$('.userList').empty().append(conter);
			});
		},
		// 添加绑定视图
		addweChatView:function(){
			$('.iconCode').show();
			$('.personalDetails').hide();
			this.getQRCode();
		},
		// 取消当前绑定
		cancelBdinding:function(uid){
			var _this = this;
			var bdinding = layer.confirm(lan.config.confirm_unbind,{
				btn:[lan.config.confirm,lan.config.cancel],
				icon:3,
				title:lan.config.unbind
			},function(){
				$.get('/wxapp?action=blind_del',{uid:uid}, function(res) {
					layer.msg(res.msg,{icon:res.status?1:2});
					_this.getUserDetails();
				});
			},function(){
				layer.close(bdinding);
			});
		},
		// 监听是否绑定
		verifyBdinding:function(){
			var _this = this;
			$.get('/wxapp?action=blind_result',function(res){
				if(res){
					layer.msg(lan.config.bind_success,{icon:1});
					clearInterval(_this.settiming);
					_this.getUserDetails();
				}
			});
		},
	}

function open_wxapp(){
	var rhtml = '<div class="boxConter" style="display: none">\
					<div class="iconCode" >\
						<div class="box-conter">\
							<div id="QRcode"></div>\
							<div class="codeTip">\
								<ul>\
									<li>1、'+lan.config.open_small_app+'<span class="btlink weChat">'+lan.config.qrcore_of_small_app+'<div class="weChatSamll"><img src="https://app.bt.cn/static/app.png"></div></span></li>\
									<li>2、'+lan.config.scan_qrcore_with_small_app+'</li>\
								</ul>\
								<span><a href="javascript:;" title="'+lan.config.return_bind_list+'" class="btlink" style="margin: 0 auto" onclick="weChat.getUserDetails(true)">'+lan.config.read_bind_list+'</a></span>\
							</div>\
						</div>\
					</div>\
					<div class="personalDetails" style="display: none">\
						<ul class="userList"></ul>\
					</div>\
				</div>'

	layer.open({
		type: 1,
		title: lan.config.bind_wechat,
		area: '500px',
		closeBtn: 2,
		shadeClose: false,
		content:rhtml
	});

	weChat.init();
}

$(function () {

     $.get("/ssl?action=GetUserInfo", function (b) {
        if (b.status) {
            $("input[name='btusername']").val(b.data.username);
            $("input[name='btusername']").next().text(lan.public.edit).attr("onclick", "bindBTName(2,'c')").css({ "right": "57px" });
            $("input[name='btusername']").next().after('<span class="modify btn btn-xs btn-success" onclick="UnboundBt()" style="vertical-align: 0px;">' + lan.config.binding_un + '</span>');
        }
        else {
            $("input[name='btusername']").next().text(lan.config.binding).attr("onclick", "bindBTName(2,'b')").removeAttr("style");

        }
        bt_init();
    });
})

function bt_init() {
    var btName = $("input[name='btusername']").val();
    //console.log(btName);
    if (!btName) {
        $('.wxapp_p .inputtxt').val(lan.config.no_bind_bt_account);
        $('.wxapp_p .modify').attr("onclick", "");
    }
}



function GetPanelApi() {
    var loadT = layer.msg(lan.config.get_api, { icon: 16, time: 0, shade: [0.3, '#000'] });
    $.post('/config?action=get_token', {}, function (rdata) {
        layer.close(loadT);
        isOpen = rdata.open ? 'checked' : '';
        layer.open({
            type: 1,
            area: "522px",
            title: lan.config.set_api,
            closeBtn: 2,
            shift: 5,
            shadeClose: false,
			content: ' <div class="bt-form bt-form" style="padding:15px 25px">\
						<div class="line">\
							<span class="tname">'+lan.config.api+'</span>\
							<div class="info-r" style="height:28px;">\
								<input class="btswitch btswitch-ios" id="panelApi_s" type="checkbox" '+ isOpen+'>\
								<label style="position: relative;top: 5px;" class="btswitch-btn" for="panelApi_s" onclick="SetPanelApi(2,1)"></label>\
							</div>\
						</div>\
                        <div class="line">\
                            <span class="tname">'+lan.config.int_sk+'</span>\
                            <div class="info-r">\
                                <input readonly="readonly" name="panel_token_value" class="bt-input-text mr5 disable" type="text" style="width: 310px" value="'+rdata.token+'" disable>\
                                <button class="btn btn-xs btn-success btn-sm" style="margin-left: -57px;" onclick="SetPanelApi(1)">'+lan.config.reset+'</button>\
                            </div>\
                        </div>\
                        <div class="line ">\
                            <span class="tname" style="overflow: initial;height:20px;line-height:20px;">'+lan.config.ip_white_list+'</br>('+lan.config.one_per_line+')</span>\
                            <div class="info-r">\
                                <textarea name="api_limit_addr" class="bt-input-text mr5" type="text" style="width: 310px;height:80px;line-height: 20px;padding: 5px 8px;margin-bottom:10px;">'+ rdata.limit_addr +'</textarea>\
                                <button class="btn btn-success btn-sm" onclick="SetPanelApi(3)">'+lan.config.save+'</button>\
                            </div>\
                        </div>\
                        <ul class="help-info-text c7">\
                            <li>'+lan.config.help1+'</li>\
                            <li>'+lan.config.help2+'</li>\
                            <li>'+lan.config.help3+'：<a class="btlink" href="https://forum.aapanel.com/d/482-api-interface-tutorial" target="_blank">https://forum.aapanel.com/d/482-api-interface-tutorial</a></li>\
                        </ul>\
                    </div>'
        })
    });
}
function showPawApi(){
	layer.msg('The panel API key only supports one-time display, please keep it safe. <br>To display the panel API key, click the reset button to regain the new API key.<br><span style="color:red;">Note: After the key is reset, the associated key product will be invalid. Please re-add the new key to the product.</span>',{icon:0,time:0,shadeClose:true,shade:0.1});
}


function SetPanelApi(t_type,index) {
    var pdata = {}
    pdata['t_type'] = t_type
    if (t_type == 3) {
        pdata['limit_addr'] = $("textarea[name='api_limit_addr']").val()
    }
    if(t_type == 1){
    	var bdinding = layer.confirm('Are you sure you want to reset your current key?<br><span style="color:red;">After the key is reset, the associated key product will be invalid. Please re-add the new key to the product.</span>',{
			btn:['Confirm','Cancel'],
			icon:3,
			closeBtn: 2,
			title:'Reset key'
		},function(){
		    var loadT = layer.msg(lan.config.is_submitting, { icon: 16, time: 0, shade: [0.3, '#000'] });
		    set_token_req(pdata,function(rdata){
	    		if (rdata.status) {
	                $("input[name='panel_token_value']").val(rdata.msg);
	                layer.msg(lan.config.create_int_key_success, { icon: 1, time: 0, shade: 0.3, shadeClose:true,closeBtn:2});
	            }else{
	            	layer.msg(rdata.msg, { icon: 2});
	            }
	            return false;
		    });
		});
		return false
    }
    set_token_req(pdata,function(rdata){
		layer.close(layer.index);
        if (rdata.msg == 'Open success!') {
            if(t_type == 2 && index != '1') GetPanelApi();
		}
		if(t_type == 2) $('#panelApi').prop('checked',rdata.msg == 'Open success!'?true:false);
		layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
    });
}

function set_token_req(pdata,callback){
	$.post('/config?action=set_token', pdata, function (rdata) {
		if(callback) callback(rdata);
	});
}



function SetIPv6() {
    var loadT = layer.msg(lan.config.setting_up, { icon: 16, time: 0, shade: [0.3, '#000'] });
    $.post('/config?action=set_ipv6_status', {}, function (rdata) {
        layer.close(loadT);
        bt.msg(rdata);
    });
}


function modify_basic_auth_to() {
    var pdata = {
        open: $("select[name='open']").val(),
        basic_user: $("input[name='basic_user']").val(),
        basic_pwd: $("input[name='basic_pwd']").val()
    }
    var loadT = layer.msg(lan.config.set_basicauth, { icon: 16, time: 0, shade: [0.3, '#000'] });
    $.post('/config?action=set_basic_auth', pdata, function (rdata) {
        layer.close(loadT);
        if (rdata.status) {
            layer.closeAll();
            setTimeout(function () { window.location.reload(); }, 3000);
        }
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
    });

}
function set_panel_report(){
	if(!three_channel_status.user_mail.user_name) return layer.msg('Please set up the [ Notification ] first',{icon:2})
	get_login_send(function(rdata){
		layer.open({
			type: 1,
			area:'700px',
			title: "Login panel alarm",
			closeBtn: 2,
			shift: 5,
			shadeClose: false,
			content: '<div class="bt-form">\
						<div class="bt-w-main">\
							<div class="bt-w-menu" style="width: 140px;">\
								<p class="bgw">Alarm settings</p>\
								<p>IP whitelist</p>\
							</div>\
							<div class="bt-w-con pd15" style="margin-left: 140px;">\
								<div class="plugin_body">\
									<div class="conter_box active" >\
										<div class="bt-form" style="height:500px">\
											<div class="line">\
												<span class="set-tit" style="display:inline-block;vertical-align: top;margin: 3px;color:#666" title="Notification email">Send to mailbox</span>\
												<div class="mail" name="server_input" style="display:inline-block;margin:0px 10px 0px 0px">\
													<input class="btswitch btswitch-ios" id="mail" type="checkbox" '+(!rdata.status?"":(rdata.msg.mail?"checked":""))+' >\
													 <label class="btswitch-btn" for="mail"></label>\
												</div>\
											</div>\
											<div class="line" style="max-height:400px;height:auto;overflow:auto">\
												<div class="divtable">\
													<table class="table table-hover" width="100%" cellspacing="0" cellpadding="0" border="0"><thead><tr><th width="75%">login info</th><th width="25%" style="text-align:right">time</th></tr></thead>\
													 <tbody id="server_table"></tbody>\
													</table>\
												</div>\
											</div>\
											<div class="page" id="server_table_page"></div>\
										</div>\
										<ul class="mtl0 c7" style="font-size: 13px;position:absolute;bottom:0;padding-right: 40px;">\
										   <li style="list-style:inside disc">xxxxxxxxxxxxxxxxxxx</li>\
										</ul>\
									</div>\
									<div class="conter_box" style="display:none;height:500px">\
										<div class="bt-form">\
											<div class="line" style="display:inline-block">\
												<input name="ip_write" class="bt-input-text mr5" type="text" style="width: 220px;" placeholder="Please enter the IP">\
												<button class="btn btn-success btn-sm add_ip_write" style="padding: 4px 15px">Add</button>\
											</div>\
											<div class="line" style="float:right">\
												<button class="btn btn-default btn-sm clear_all" style="padding: 4px 15px;text-align:right">Clean all</button>\
											</div>\
											 <div class="line" style="max-height:400px;height:auto;overflow:auto">\
												<div class="divtable">\
													<table class="table table-hover" width="100%" cellspacing="0" cellpadding="0" border="0"><thead><tr><th width="60%">IP</th><th width="40%" style="text-align:right">Opt</th></tr></thead>\
													 <tbody id="ip_write_table"></tbody>\
													</table>\
												</div>\
											</div>\
										</div>\
										  <ul class="mtl0 c7" style="font-size: 13px;position:absolute;bottom:0;padding-right: 40px;">\
										   <li style="list-style:inside disc">Only allow to set ipv4 whitelist</li>\
										</ul>\
									</div>\
								</div>\
							</div>\
						</div>\
					  </div>',
			success:function(index,layers){
				get_log_table();
				get_ip_write_table()
				$(".bt-w-menu p").click(function () {
					var index = $(this).index();
					$(this).addClass('bgw').siblings().removeClass('bgw');
					console.log(index,'111');
					switch(index){
						case 0:
							get_log_table();
							break;
						case 1:
							get_ip_write_table()
							break;
					}
					$('.conter_box').eq(index).show().siblings().hide();
				});
				//设置告警
				$('#mail').on('click',function(){
					var _checked = $(this).prop('checked');
					if(_checked){
						$.post('/config?action=set_login_send',{type:'mail'},function(res){
							layer.msg(res.msg,{icon:res.status?1:2});
						});
					}else{
						$.post('/config?action=clear_login_send',{type:'mail'},function(res){
							layer.msg(res.msg,{icon:res.status?1:2});
						});
					}
				});
				//添加
				$('.add_ip_write').on('click',function(){
					var _ip = $('[name="ip_write"]').val();
					if(!bt.check_ip(_ip)) return layer.msg('Please enter the correct IP',{icon:2})
					login_ipwhite({ip:_ip,type:'add'},function(res){
						if(res.status) get_ip_write_table()
						layer.msg(res.msg,{icon:res.status?1:2});
					})
				})
				//删除ip白名单
				$('#ip_write_table').on('click','.del_ip_write',function(){
					var _ip = $(this).parents('tr').data().data;
					login_ipwhite({ip:_ip,type:'del'},function(res){
						if(res.status) get_ip_write_table()
						layer.msg(res.msg,{icon:res.status?1:2});
					})
				});
				//清空全部
				$('.clear_all').on('click',function(){
					layer.confirm('Whether to clear the IP whitelist', {title:'Tips',btn: ['Confirm','Cancel'],icon:0,closeBtn:2}, function() {
						login_ipwhite({type:'clear'},function(res){
							if(res.status) get_ip_write_table()
							layer.msg(res.msg,{icon:res.status?1:2});
						})
					})
				})
				//分页操作
				$('#server_table_page').on('click','a',function(e){
					e.stopPropagation();
					e.preventDefault();
					var _p = $(this).attr('href').match(/p=([0-9]*)/)[1];
					get_log_table({p:_p});
				})
			},
			cancel:function(){
				$('#panel_report').val( $('#mail').prop('checked') ? 'Already set' : 'Not set');
			}
		})
	})
}
function get_log_table(obj){
    if(!obj) obj = {p:1}
    var loadT = bt.load('Getting Logs list, please wait')
	$.post('/config?action=get_login_log',obj,function(res){
		loadT.close()
        $('#server_table').empty()
		if(res.data.length > 0){
			$.each(res.data,function(index,item){
				$('#server_table').append($('<tr>\
					<td>'+ item.log +'</td>\
					<td style="text-align:right">'+ item.addtime +'</td>\
					</tr>').data({data:item,index:index}))
			});
		}else{
			$('#server_table').html('<tr><td colspan="2" style="text-align:center">None Data</td></tr>')
		}
		$('#server_table_page').html(res.page)
	});
}
function get_ip_write_table(){
    $('#ip_write_table').empty()
    login_ipwhite({type:'get'},function(res){
		if(res.msg.length > 0){
			$.each(res.msg,function(index,item){
				$('#ip_write_table').append($('<tr>\
					<td>'+ item +'</td>\
					<td style="text-align:right">\
						<a href="javascript:;" class="btlink del_ip_write" >Del</a>\
					</td>\
					</tr>').data({data:item,index:index}))
			});
		}else{
			$('#ip_write_table').html('<tr><td colspan="2" style="text-align:center">None Data</td></tr>')
		}
    })
}
function modify_basic_auth() {
    var loadT = layer.msg(lan.config.setting_basicauth, { icon: 16, time: 0, shade: [0.3, '#000'] });
    $.post('/config?action=get_basic_auth_stat', {}, function (rdata) {
        layer.close(loadT);
        if (rdata.open) {
            show_basic_auth(rdata);
        } else {
            m_html = '<div class="risk_form"><i class="layui-layer-ico layui-layer-ico3"></i>'
                + '<h3 class="risk_tilte">Warning! Do not understand this feature, do not open!</h3>'
                + '<ul style="border: 1px solid #ececec;border-radius: 10px; margin: 0px auto;margin-top: 20px;margin-bottom: 20px;background: #f7f7f7; width: 100 %;padding: 33px;list-style-type: inherit;">'
					+ '<li style="color:red;">You must use and understand this feature to decide if you want to open it!</li>'
					+ '<li>After opening, access the panel in any way, you will be asked to enter the BasicAuth username and password first.</li>'
					+ '<li>After being turned on, it can effectively prevent the panel from being scanned and found, but it cannot replace the account password of the panel itself.</li>'
					+ '<li>Please remember the BasicAuth password, but forget that you will not be able to access the panel.</li>'
					+ '<li>If you forget your password, you can disable BasicAuth authentication by using the bt command in SSH.</li>'
                + '</ul></div>'
                + '<div class="details">'
                + '<input type="checkbox" id="check_basic"><label style="font-weight: 400;margin: 3px 10px 0px;font-size:12px;" for="check_basic">I already know the details and are willing to take risks</label>'
                + '<a target="_blank" style="font-size:12px;" class="btlink" href="https://www.bt.cn/bbs/thread-34374-1-1.html">What is BasicAuth authentication?</a><p></p></div>'
            var loadT = layer.confirm(m_html, { title: "Risk reminder", area: "600px",closeBtn:2 }, function () {
                if (!$("#check_basic").prop("checked")) {
                    layer.msg("Please read the precautions carefully and check to agree to take risks!");
                    setTimeout(function () { modify_basic_auth();},3000)
                    return;
                }
                layer.close(loadT)
                show_basic_auth(rdata);
            });

        }
    });
}
function open_three_channel_auth(){
	get_channel_settings(function(rdata){
		var isOpen = rdata.dingding.info.msg.isAtAll == 'True' ? 'checked': '';
		var isDing = rdata.dingding.info.msg == 'No information'? '': rdata.dingding.info.msg.dingding_url;
		layer.open({
			type: 1,
	        area: "600px",
	        title: "Setting up notification",
	        closeBtn: 2,
	        shift: 5,
	        shadeClose: false,
	        content: '<div class="bt-form mes_channel">\
	        			<div class="bt-w-main">\
					        <div class="bt-w-menu">\
					            <p class="bgw">Email</p>\
					        </div>\
					        <div class="bt-w-con pd15">\
					            <div class="plugin_body">\
	                				<div class="conter_box active" >\
	                					<div class="bt-form">\
	                						<div class="line">\
	                							<button class="btn btn-success btn-sm" onclick="add_receive_info()">Add recipient</button>\
	                							<button class="btn btn-default btn-sm" onclick="sender_info_edit()">Sender settings</button>\
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
		                				<div class="bt-form">\
		                					<div class="line">\
												<span class="tname">Notice all</span>\
												<div class="info-r" style="height:28px; margin-left:125px">\
													<input class="btswitch btswitch-ios" id="panel_alert_all" type="checkbox" '+ isOpen+'>\
													<label style="position: relative;top: 5px;" class="btswitch-btn" for="panel_alert_all"></label>\
												</div>\
											</div>\
						        			<div class="line">\
					                            <span class="tname">DingDing URL</span>\
					                            <div class="info-r">\
					                                <textarea name="channel_dingding_value" class="bt-input-text mr5" type="text" style="width: 300px; height:90px; line-height:20px">'+isDing+'</textarea>\
					                            </div>\
					                            <button class="btn btn-success btn-sm" onclick="SetChannelDing()" style="margin: 10px 0 0 125px;">Save</button>\
					                        </div>\
				                        </div>\
		            				</div>\
	                			</div>\
	                		</div>\
                		</div>\
                	  </div>'
		})
		$(".bt-w-menu p").click(function () {
            var index = $(this).index();
            $(this).addClass('bgw').siblings().removeClass('bgw');
            $('.conter_box').eq(index).show().siblings().hide();
        });
		get_receive_list();
	})
}
function sender_info_edit(){
	var loadT = layer.msg('Getting profile, please wait...', { icon: 16, time: 0, shade: [0.3, '#000'] });
	$.post('/config?action=get_settings',function(rdata){
		layer.close(loadT);
		var qq_mail = rdata.user_mail.info.msg.qq_mail == undefined ? '' : rdata.user_mail.info.msg.qq_mail,
			qq_stmp_pwd = rdata.user_mail.info.msg.qq_stmp_pwd == undefined? '' : rdata.user_mail.info.msg.qq_stmp_pwd,
			hosts = rdata.user_mail.info.msg.hosts == undefined? '' : rdata.user_mail.info.msg.hosts,
			port = rdata.user_mail.info.msg.port == undefined? '' : rdata.user_mail.info.msg.port;
		layer.open({
		type: 1,
        area: "485px",
        title: "Set sender email information",
        closeBtn: 2,
        shift: 5,
        shadeClose: false,
        content: '<div class="bt-form pd20 pb70">\
        	<div class="line">\
                <span class="tname">Sender email</span>\
                <div class="info-r">\
                    <input name="channel_email_value" class="bt-input-text mr5" type="text" style="width: 300px" value="'+qq_mail+'">\
                </div>\
            </div>\
            <div class="line">\
                <span class="tname">smtp password</span>\
                <div class="info-r">\
                    <input name="channel_email_password" class="bt-input-text mr5" type="password" style="width: 300px" value="'+qq_stmp_pwd+'">\
                </div>\
            </div>\
            <div class="line">\
                <span class="tname">smtp server</span>\
                <div class="info-r">\
                    <input name="channel_email_server" class="bt-input-text mr5" type="text" style="width: 300px" value="'+hosts+'">\
                </div>\
			</div>\
			<div class="line">\
                <span class="tname">smtp port</span>\
                <div class="info-r">\
                    <select class="bt-input-text mr5" id="port_select" style="width:'+(select_port(port)?'300px':'100px')+'"></select>\
                    <input name="channel_email_port" class="bt-input-text mr5" type="Number" style="display:'+(select_port(port)? 'none':'inline-block')+'; width: 190px" value="'+port+'">\
                </div>\
            </div>\
            <ul class="help-info-text c7">\
            	<li>465 port is recommended, the protocol is SSL/TLS</li>\
            	<li>Port 25 is SMTP protocol, port 587 is STARTTLS protocol</li>\
            </ul>\
            <div class="bt-form-submit-btn">\
	            <button type="button" class="btn btn-danger btn-sm smtp_closeBtn">Close</button>\
	            <button class="btn btn-success btn-sm SetChannelEmail">Save</button></div>\
        	</div>',
        success:function(layers,index){
			var _option = '';
        	if(select_port(port)){
        		if(port == '465' || port == ''){
        			_option = '<option value="465" selected="selected">465</option><option value="25">25</option><option value="587">587</option><option value="other">Customize</option>'
        		}else if(port == '25'){
        			_option = '<option value="465">465</option><option value="25" selected="selected">25</option><option value="587">587</option><option value="other">Customize</option>'
        		}else{
        			_option = '<option value="465">465</option><option value="25">25</option><option value="587" selected="selected">587</option><option value="other">Customize</option>'
        		}
        	}else{
        		_option = '<option value="465">465</option><option value="25">25</option><option value="587" >587</option><option value="other" selected="selected">Customize</option>'
        	}
        	$("#port_select").html(_option)
        	$("#port_select").change(function(e){
        		if(e.target.value == 'other'){
        			$("#port_select").css("width","100px");
					$('input[name=channel_email_port]').css("display","inline-block");
        		}else{
        			$("#port_select").css("width","300px");
					$('input[name=channel_email_port]').css("display","none");
        		}
        	})
			$(".SetChannelEmail").click(function(){
				var _email = $('input[name=channel_email_value]').val();
				var _passW = $('input[name=channel_email_password]').val();
				var _server = $('input[name=channel_email_server]').val();
				if($('#port_select').val() == 'other'){
					_port = $('input[name=channel_email_port]').val();
				}else{
					_port = $('#port_select').val()
				}
				if(_email == ''){
					return layer.msg('Email address cannot be empty!',{icon:2});
				}else if(_passW == ''){
					return layer.msg('STMP password cannot be empty!',{icon:2});
				}else if(_server == ''){
					return layer.msg('STMP server address cannot be empty!',{icon:2});
				}else if(_port == ''){
					return layer.msg('STMP server port cannot be empty!',{icon:2});
				}
				var loadT = layer.msg('The notification is being generated, please wait...', { icon: 16, time: 0, shade: [0.3, '#000'] });
				layer.close(index)
				$.post('/config?action=user_mail_send',{email:_email,stmp_pwd:_passW,hosts:_server,port:_port},function(rdata){
					layer.close(loadT);
					layer.msg(rdata.msg,{icon:rdata.status?1:2})
				})
			})
			$(".smtp_closeBtn").click(function(){
				layer.close(index)
			})
		}
	})
	});
}
function select_port(port){
	switch(port){
		case '25':
			return true;
		case '465':
			return true;
		case '587':
			return true;
		case '':
			return true;
		default:
			return false
	}
}
function get_channel_settings(callback){
	var loadT = layer.msg('Getting profile, please wait...', { icon: 16, time: 0, shade: [0.3, '#000'] });
	$.post('/config?action=get_settings',function(rdata){
		layer.close(loadT);
        if (callback) callback(rdata);
	})
}
function add_receive_info(){
	layer.open({
		type: 1,
        area: "400px",
        title: "Add recipient email",
        closeBtn: 2,
        shift: 5,
        shadeClose: false,
        content: '<div class="bt-form pd20 pb70">\
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
        success:function(layers,index){
        	$(".CreaterReceive").click(function(){
        		var _receive = $('input[name=creater_email_value]').val(),_that = this;
				if(_receive != ''){
					var loadT = layer.msg('Please wait while creating recipient list...', { icon: 16, time: 0, shade: [0.3, '#000'] });
					layer.close(index)
					$.post('/config?action=add_mail_address',{email:_receive},function(rdata){
						layer.close(loadT);
						// 刷新收件列表
						get_receive_list();
						layer.msg(rdata.msg,{icon:rdata.status?1:2});
					})
				}else{
					layer.msg('Recipient mailbox cannot be empty！',{icon:2});
				}
        	})

			$(".smtp_closeBtn").click(function(){
				layer.close(index)
			})
		}
	})
}
function get_receive_list(){
	$.post('/config?action=get_settings',function(rdata){
		var _html = '',_list = rdata.user_mail.mail_list;
		if(_list.length > 0){
			for(var i= 0; i<_list.length;i++){
				_html += '<tr>\
					<td>'+ _list[i] +'</td>\
					<td width="80px"><a onclick="del_email(\''+ _list[i] + '\')" href="javascript:;" style="color:#20a53a">Del</a></td>\
					</tr>'
			}
		}else{
			_html = '<tr>No Data</tr>'
		}
		$('#receive_table').html(_html);
	})

}

function del_email(mail){
	var loadT = layer.msg('Deleting ['+ mail +'], please wait...', { icon: 16, time: 0, shade: [0.3, '#000'] }),_this = this;
	$.post('/config?action=del_mail_list',{email:mail},function(rdata){
		layer.close(loadT);
		layer.msg(rdata.msg,{icon:rdata.status?1:2})
		_this.get_receive_list()
	})
}
// 设置钉钉
function SetChannelDing(){
	var _url = $('textarea[name=channel_dingding_value]').val();
	var _all = $('#panel_alert_all').prop("checked");
	if(_url != ''){
		var loadT = layer.msg('Please wait while generating dingding channel...', { icon: 16, time: 0, shade: [0.3, '#000'] });
		$.post('/config?action=set_dingding',{url:_url,atall:_all == true? 'True':'False'},function(rdata){
			layer.close(loadT);
			layer.msg(rdata.msg,{icon:rdata.status?1:2})
		})
	}else{
		layer.msg('Please enter the dingding URL',{icon:2})
	}
}



function show_basic_auth(rdata) {
    layer.open({
        type: 1,
        area: "500px",
        title: "Configure BasicAuth authentication",
        closeBtn: 2,
        shift: 5,
        shadeClose: false,
        content: ' <div class="bt-form bt-form" style="padding:15px 25px">\
						<div class="line">\
							<span class="tname">'+lan.public.server_status+'</span>\
							<div class="info-r" style="height:28px;">\
								<select class="bt-input-text" name="open">\
                                    <option value="True" '+(rdata.open?'selected':'')+'>'+lan.public.on+'</option>\
                                    <option value="False" '+ (rdata.open ? '' : 'selected' )+'>'+lan.public.off+'</option>\
                                </select>\
							</div>\
						</div>\
                        <div class="line">\
                            <span class="tname">'+lan.public.username+'</span>\
                            <div class="info-r">\
                                <input name="basic_user" class="bt-input-text mr5" type="text" style="width: 310px" value="" placeholder="'+ (rdata.basic_user?lan.config.not_modified:lan.config.set_username) +'">\
                            </div>\
                        </div>\
                        <div class="line">\
                            <span class="tname">'+lan.public.pass+'</span>\
                            <div class="info-r">\
                                <input name="basic_pwd" class="bt-input-text mr5" type="text" style="width: 310px" value="" placeholder="'+ (rdata.basic_pwd ? lan.config.not_modified : lan.config.set_passwd) +'">\
                            </div>\
                        </div>\
                        <span><button class="btn btn-success btn-sm" style="    margin-left: 340px;" onclick="modify_basic_auth_to()">'+lan.public.save+'</button></span>\
                        <ul class="help-info-text c7">\
                            <li style="color:red;">'+lan.config.basic_auth_tips1+'</li>\
                            <li>'+lan.config.basic_auth_tips2+'</li>\
                            <li>'+lan.config.basic_auth_tips3+'</li>\
                        </ul>\
                    </div>'
    })
}
function get_panel_hide_list(){
	var loadT = bt.load('Getting panel menu bar, please wait...'),arry = [];
	$.post('/config?action=get_menu_list',function(rdata){
		loadT.close();
		$.each(rdata,function(index,item){
			if(!item.show) arry.push(item.title)
		});
		$('#panel_menu_hide').val(arry.length > 0?arry.join('/'):'No hidden bar');
	});

}

get_panel_hide_list();

// 设置面板菜单显示功能
function set_panel_ground(){
	var loadT = bt.load('Getting panel menu bar, please wait...');
	$.post('/config?action=get_menu_list',function(rdata){
		var html = '',arry = ["dologin","memuAconfig","memuAsoft","memuA"],is_option = '';
		loadT.close();
		$.each(rdata,function(index,item){
			is_option = '<div class="index-item" style="float:right;"><input class="btswitch btswitch-ios" id="'+ item.id +'0000" name="'+ item.id +'" type="checkbox" '+ (item.show?'checked':'') +'><label class="btswitch-btn" for="'+ item.id +'0000"></label></div>'
			
			if(item.id == 'dologin' || item.id == 'memuAconfig' || item.id == 'memuAsoft' || item.id == 'memuA') is_option = 'Inoperable';
			html += '<tr><td>'+ item.title +'</td><td><div style="float:right;">'+ is_option +'</div></td></tr>';
		});
		layer.open({
			type:1,
			title:'Manage panel menu bar',
			area:['350px','536px'],
			shadeClose:false,
			closeBtn:2,
			content:'<div class="divtable softlist" id="panel_menu_tab" style="padding: 20px 15px;"><table class="table table-hover"><thead><tr><th>Menu bar</th><th style="text-align:right;width:120px;">Display</th></tr></thead><tbody>'+ html +'</tbody></table></div>',
			success:function(){
				$('#panel_menu_tab input').click(function(){
					var arry = [];
					$(this).parents('tr').siblings().each(function(index,el){
						if($(this).find('input').length >0 && !$(this).find('input').prop('checked')){
							arry.push($(this).find('input').attr('name'));
						}
					});
					if(!$(this).prop('checked')){
						arry.push($(this).attr('name'));
					}
					var loadT = bt.load('Setting panel menu bar display status, please wait...');
					$.post('/config?action=set_hide_menu_list',{hide_list:JSON.stringify(arry)},function(rdata){
						loadT.close();
						bt.msg(rdata);
					});
				});
			}
		});
	});
}


/**
 * @description 获取临时授权列表
 * @param {Function} callback 回调函数列表
 * @returns void
 */
function get_temp_login(data,callback){
	var loadT = bt.load('Get temporary authorization list, please wait...');
	bt.send('get_temp_login','config/get_temp_login',data,function(res){
		if(res.status === false){
			layer.closeAll();
			bt.msg(res);
			return false;
		}
		loadT.close();
		if(callback) callback(res)
	});
}

/**
 * @description 设置临时链接
 * @param {Function} callback 回调函数列表
 * @returns void
 */
function set_temp_login(callback){
	var loadT = bt.load('Setting temporary links, please wait...');
	bt.send('set_temp_login','config/set_temp_login',{},function(res){
		loadT.close();
		if(callback) callback(res)
	});
}

/**
 * @description 设置临时链接
 * @param {Object} data 传入参数，id
 * @param {Function} callback 回调函数列表
 * @returns void
*/
function remove_temp_login(data,callback){
	var loadT = bt.load('Deleting temporary authorization record, please wait...');
	bt.send('remove_temp_login','config/remove_temp_login',{id:data.id},function(res){
		loadT.close();
		if(callback) callback(res)
	});
}
/**
 * @description 强制用户登出
 * @param {Object} data 传入参数，id
 * @param {Function} callback 回调函数列表
 * @returns void
*/
function clear_temp_login(data,callback){
	var loadT = bt.load('Forcing user to log out, please wait...');
	bt.send('clear_temp_login','config/clear_temp_login',{id:data.id},function(res){
		loadT.close();
		if(callback) callback(res)
	});
}

/**
 * @description 渲染授权管理列表
 * @param {Object} data 传入参数，id
 * @param {Function} callback 回调函数列表
 * @returns void
*/
function reader_temp_list(data,callback){
	if(typeof data == 'function') callback = data,data = {p:1};
	get_temp_login(data,function(rdata){
		var html = '';
		$.each(rdata.data,function(index,item){
			html += '<tr><td>'+ (item.login_addr || 'Not login') +'</td><td>'+ (function(){
				switch(item.state){
					case 0:
						return 'Not login';
					break;
					case 1:
						return 'Logged in';
					break;
					case -1:
						return 'Expired';
					break;
				}
			}()) +'</td><td >'+ (item.login_time == 0?'Not login':bt.format_data(item.login_time)) +'</td><td>'+ bt.format_data(item.expire) +'</td><td style="text-align:right;">'+ (function(){
				if(item.state != 1){
					return '<a href="javascript:;" class="btlink remove_temp_login" data-ip="'+ item.login_addr +'" data-id="'+ item.id +'">Del</a>';
				}
				if(item.online_state){
					return '<a href="javascript:;" class="btlink clear_temp_login" style="color:red" data-ip="'+ item.login_addr +'" data-id="'+ item.id +'">Force logout </a>&nbsp;&nbsp;|&nbsp;&nbsp;<a href="javascript:;" class="btlink logs_temp_login" data-ip="'+ item.login_addr +'" data-id="'+ item.id +'">Logs</a>';
				}
				return '<a href="javascript:;" class="btlink logs_temp_login" data-ip="'+ item.login_addr +'" data-id="'+ item.id +'">Logs</a>';
			}()) +'</td></tr>';
		});
		$('#temp_login_view_tbody').html(html);
		$('.temp_login_view_page').html(rdata.page);
		if(callback) callback()
	});
}




/**
 * @description 获取操作日志
 * @param {Object} data 传入参数，id
 * @param {Function} callback 回调函数列表
 * @returns void
*/
function get_temp_login_logs(data,callback){
	var loadT = bt.load('Getting operation log, please wait...');
	bt.send('clear_temp_login','config/get_temp_login_logs',{id:data.id},function(res){
		loadT.close();
		if(callback) callback(res)
	});
}

/**
 * @description 渲染操作日志
 * @param {Object} data 传入参数，id
 * @param {Function} callback 回调函数列表
 * @returns void
*/
function reader_temp_login_logs(data,callback){
	get_temp_login_logs(data,function(res){
		var html = '';
		$.each(res,function(index,item){
			html += '<tr><td>'+ item.type +'</td><td>'+ item.addtime +'</td><td><span title="'+ item.log +'" style="white-space: pre;">'+ item.log +'</span></td></tr>';
		});
		if(callback) callback({tbody:html,data:res});
	})
}




/**
 * @description 设置临时链接
 * @param {Function} callback 回调函数列表
 * @returns void
*/
function get_temp_login_view(){
	layer.open({
		type: 1,
        area:["700px",'600px'],
        title: "Temporary authorization management",
        closeBtn: 2,
        shift: 5,
		shadeClose: false,
		content:'<div class="login_view_table pd15">'+
			'<button class="btn btn-success btn-sm va0 create_temp_login" >Create authorization</button>'+
			'<div class="divtable mt10">'+
				'<table class="table table-hover">'+
					'<thead><tr><th>Login IP</th><th>Status</th><th>Login time</th><th>Expiration time</th><th style="text-align:right;">Opt</th></tr></thead>'+
					'<tbody id="temp_login_view_tbody"></tbody>'+
				'</table>'+
				'<div class="temp_login_view_page page"></div>'+
			'</div>'+
		'</div>',
		success:function(){
			reader_temp_list();
			// 创建临时授权
			$('.create_temp_login').click(function(){
				bt.confirm({title:'Risk tips',msg:'<span style="color:red">Note 1: Abuse of temporary authorization may lead to security risks.</br>Note 2: Not publish temporary authorized connections in public</span></br>Temporary authorization connection is about to be created. Continue?'},function(){
					layer.open({
						type: 1,
						area:'570px',
						title: "Create temporary authorization",
						closeBtn: 2,
						shift: 5,
						shadeClose: false,
						content:'<div class="bt-form create_temp_view">'+
							'<div class="line"><span class="tname" style="width: auto;">Temporary authorized address</span><div class="info-r ml0"><textarea id="temp_link" class="bt-input-text mr20" style="margin: 0px;width: 500px;height: 50px;line-height: 19px;"></textarea></div></div>'+
							'<div class="line"><button type="submit" class="btn btn-success btn-sm btn-copy-temp-link" data-clipboard-text="">Copy address</button></div>'+
							'<ul class="help-info-text c7"><li>The temporary authorization is valid within 1 hour after it is generated. It is a one-time authorization and will be invalid immediately after use</li><li>Use temporary authorization to log in to the panel within 1 hour. Do not publish temporary authorization connection in public</li><li>The authorized connection information is only displayed here once. If you forget it before use, please regenerate it</li></ul>'+
						'</div>',
						success:function(){
							set_temp_login(function(res){
								if(res.status){
									var temp_link = location.origin+ '/login?tmp_token=' + res.token;
									$('#temp_link').val(temp_link);
									$('.btn-copy-temp-link').attr('data-clipboard-text',temp_link);
								}
							});
							var clipboard = new ClipboardJS('.btn');
							clipboard.on('success', function(e) {
								bt.msg({status:true,msg:'Copy succeeded!'});
								e.clearSelection();
							});
							clipboard.on('error', function(e) {
								bt.msg({status:false,msg:'Copy failed, please copy address manually'});
							});
						},
						end:function(){
							reader_temp_list();
						}
					});
				});
			});
			// 操作日志
			$('#temp_login_view_tbody').on('click','.logs_temp_login',function(){
				var id = $(this).data('id'),ip = $(this).data('ip');
				layer.open({
					type: 1,
					area:['700px','550px'],
					title:'Operation logs ['+ ip +']',
					closeBtn: 2,
					shift: 5,
					shadeClose: false,
					content:'<div class="pd15">'+
						'<button class="btn btn-default btn-sm va0 refresh_login_logs">Refresh logs</button>'+
						'<div class="divtable mt10 tablescroll" style="max-height: 420px;overflow-y: auto;border:none">'+
							'<table class="table table-hover" id="logs_login_view_table">'+
								'<thead><tr><th width="90px">Operation</th><th width="150px">Time</th><th>logs</th></tr></thead>'+
								'<tbody ></tbody>'+
							'</table>'+
						'</div>'+
					'</div>',
					success:function(){
						reader_temp_login_logs({id:id},function(data){
							$('#logs_login_view_table tbody').html(data.tbody);
						});
						$('.refresh_login_logs').click(function(){
							reader_temp_login_logs({id:id},function(data){
								$('#logs_login_view_table tbody').html(data.tbody);
							});
						});
						bt.fixed_table('logs_login_view_table');
					}
				});
			});

			

			//删除授权记录，仅未使用的授权记录
			$('#temp_login_view_tbody').on('click','.remove_temp_login',function(){
				var id = $(this).data('id');
				bt.confirm({
					title:'Remove unused licenses',
					msg:'Delete unused authorization record, continue?'
				},function(){
					remove_temp_login({id:id},function(res){
						reader_temp_list(function(){
							bt.msg(res);
						})
					})
				})
			});
			//强制下线，强制登录的用户下线
			$('#temp_login_view_tbody').on('click','.clear_temp_login',function(){
				var id = $(this).data('id'),ip= $(this).data('ip');
				bt.confirm({
					title:'Force logout [ '+ ip +' ]',
					msg:'Confirm to force logout [ '+ ip +' ]?'
				},function(){
					clear_temp_login({id:id},function(res){
						reader_temp_list(function(){
							bt.msg(res);
						});
					});
				})
			});
			// 分页操作
			$('.temp_login_view_page').on('click','a',function(ev){
				var href = $(this).attr('href'),reg = /([0-9]*)$/,page = reg.exec(href)[0];
				reader_temp_list({p:page});
				ev.stopPropagation();
				ev.preventDefault();
			});
		}
	});

}