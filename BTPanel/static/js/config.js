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

(function(){
	check_two_step(function(res){
		$('#panel_verification').prop('checked',res.status);
	});
	get_three_channel(function(res){
		$('#channel_auth').val(!res.user_mail.user_name && !res.dingding.dingding ? 'Email is not set':(res.user_mail.user_name? 'Email is set':(res.dingding.dingding? 'dingding is set': '')))
	});
})()

function get_three_channel(callback){
	$.post('/config?action=get_settings',function(res){
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
		content: "<div class='bt-form pd20 pb70'><div class='line'><span class='tname'>"+lan.public.user+"</span><div class='info-r'><input class='bt-input-text' type='text' name='username' id='p1' value='' placeholder='"+lan.config.user_bt+"' style='width:100%'/></div></div><div class='line'><span class='tname'>"+lan.public.pass+"</span><div class='info-r'><input class='bt-input-text' type='password' name='password' id='p2' value='' placeholder='"+lan.config.pass_bt+"' style='width:100%'/></div></div><div class='bt-form-submit-btn'><button type='button' class='btn btn-danger btn-sm' onclick=\"layer.closeAll()\">"+lan.public.cancel+"</button> "+btn+"</div></div>"
	})
}
//解除绑定宝塔账号
function UnboundBt(){
	var name = $("input[name='btusername']").val();
	layer.confirm(lan.config.binding_un_msg,{closeBtn:2,icon:3,title:lan.config.binding_un},function(){
		$.get("/ssl?action=DelToken",function(b){
			layer.msg(b.msg,{icon:b.status? 1:2})
			$("input[name='btusername']").val('');
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
    var status_s = {false:'Open',true:'Close'}
    var debug_stat = $("#panelDebug").prop('checked');
    bt.confirm({
		title: status_s[debug_stat] + "Developer mode",
		msg: "Do you really want "+ status_s[debug_stat]+" developer mode?",
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
            $("input[name='btusername']").next().text(lan.public.edit).attr("onclick", "bindBTName(2,'c')").css({ "margin-left": "-82px" });
            $("input[name='btusername']").next().after('<span class="btn btn-xs btn-success" onclick="UnboundBt()" style="vertical-align: 0px;">' + lan.config.binding_un + '</span>');
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
            area: "500px",
            title: lan.config.set_api,
            closeBtn: 2,
            shift: 5,
            shadeClose: false,
			content: ' <div class="bt-form bt-form" style="padding:15px 25px">\
						<div class="line">\
							<span class="tname">'+lan.config.api+'</span>\
							<div class="info-r" style="height:28px;">\
								<input class="btswitch btswitch-ios" id="panelApi_s" type="checkbox" '+ isOpen+'>\
								<label style="position: relative;top: 5px;" class="btswitch-btn" for="panelApi_s" onclick="SetPanelApi(2)"></label>\
							</div>\
						</div>\
                        <div class="line">\
                            <span class="tname">'+lan.config.int_sk+'</span>\
                            <div class="info-r">\
                                <input readonly="readonly" name="panel_token_value" class="bt-input-text mr5 disable" type="text" style="width: 310px" value="'+rdata.token+'" disable>\
                                <button class="btn btn-xs btn-success btn-sm" style="margin-left: -50px;" onclick="SetPanelApi(1)">'+lan.config.reset+'</button>\
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
                            <li>'+lan.config.help3+'：<a class="btlink" href="https://www.bt.cn/bbs/thread-20376-1-1.html" target="_blank">https://www.bt.cn/bbs/thread-20376-1-1.html</a></li>\
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
    	layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
        if (rdata.msg == lan.config.open_successfully) {
            if(t_type == 2 && index != '0') GetPanelApi();
        }
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
	        title: "Setting up a message channel",
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
					return layer.msg('Email address cannot be empty！',{icon:2});
				}else if(_passW == ''){
					return layer.msg('STMP password cannot be empty！',{icon:2});
				}else if(_server == ''){
					return layer.msg('STMP server address cannot be empty！',{icon:2});
				}else if(_port == ''){
					return layer.msg('STMP server port cannot be empty！',{icon:2});
				}
				var loadT = layer.msg('Please wait while generating mailbox channel...', { icon: 16, time: 0, shade: [0.3, '#000'] });
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
