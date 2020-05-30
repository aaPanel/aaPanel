function IsDiskWidth() {
    var comlistWidth = $("#comlist").width();
    var bodyWidth = $(".file-box").width();
    if (comlistWidth + 530 > bodyWidth) {
        $("#comlist").css({
            "width": bodyWidth - 530 + "px",
            "height": "34px",
            "overflow": "auto"
        });
    } else {
        $("#comlist").removeAttr("style");
    }
}

function Recycle_bin(type) {
    $.post('/files?action=Get_Recycle_bin', '', function (rdata) {
        var body = '';
        switch (type) {
            case 1:
                for (var i = 0; i < rdata.dirs.length; i++) {
                    var shortwebname = rdata.dirs[i].name.replace(/'/, "\\'");
                    var shortpath = rdata.dirs[i].dname;
                    if (shortwebname.length > 20) shortwebname = shortwebname.substring(0, 20) + "...";
                    if (shortpath.length > 20) shortpath = shortpath.substring(0, 20) + "...";
                    body += '<tr>\
								<td><span class=\'ico ico-folder\'></span><span class="tname" title="' + rdata.dirs[i].name + '">' + shortwebname + '</span></td>\
								<td><span title="' + rdata.dirs[i].dname + '">' + shortpath + '</span></td>\
								<td>' + ToSize(rdata.dirs[i].size) + '</td>\
								<td>' + getLocalTime(rdata.dirs[i].time) + '</td>\
								<td style="text-align: right;">\
									<a class="btlink" href="javascript:;" onclick="ReRecycleBin(\'' + rdata.dirs[i].rname.replace(/'/, "\\'") + '\',this)">' + lan.files.recycle_bin_re + '</a>\
									 | <a class="btlink" href="javascript:;" onclick="DelRecycleBin(\'' + rdata.dirs[i].rname.replace(/'/, "\\'") + '\',this)">' + lan.files.recycle_bin_del + '</a>\
								</td>\
							</tr>';
                }
                for (var i = 0; i < rdata.files.length; i++) {
                    if (rdata.files[i].name.indexOf('BTDB_') != -1) {
                        var shortwebname = rdata.files[i].name.replace(/'/, "\\'");
                        var shortpath = rdata.files[i].dname;
                        if (shortwebname.length > 20) shortwebname = shortwebname.substring(0, 20) + "...";
                        if (shortpath.length > 20) shortpath = shortpath.substring(0, 20) + "...";
                        body += '<tr>\
								<td><span class="ico ico-' + (GetExtName(rdata.files[i].name)) + '"></span><span class="tname" title="' + rdata.files[i].name + '">' + shortwebname.replace('BTDB_', '') + '</span></td>\
								<td><span title="' + rdata.files[i].dname + '">mysql://' + shortpath.replace('BTDB_', '') + '</span></td>\
								<td>-</td>\
								<td>' + getLocalTime(rdata.files[i].time) + '</td>\
								<td style="text-align: right;">\
									<a class="btlink" href="javascript:;" onclick="ReRecycleBin(\'' + rdata.files[i].rname.replace(/'/, "\\'") + '\',this)">' + lan.files.recycle_bin_re + '</a>\
									 | <a class="btlink" href="javascript:;" onclick="DelRecycleBin(\'' + rdata.files[i].rname.replace(/'/, "\\'") + '\',this)">' + lan.files.recycle_bin_del + '</a>\
								</td>\
							</tr>'

                        continue;
                    }
                    var shortwebname = rdata.files[i].name.replace(/'/, "\\'");
                    var shortpath = rdata.files[i].dname;
                    if (shortwebname.length > 20) shortwebname = shortwebname.substring(0, 20) + "...";
                    if (shortpath.length > 20) shortpath = shortpath.substring(0, 20) + "...";
                    body += '<tr>\
								<td><span class="ico ico-' + (GetExtName(rdata.files[i].name)) + '"></span><span class="tname" title="' + rdata.files[i].name + '">' + shortwebname + '</span></td>\
								<td><span title="' + rdata.files[i].dname + '">' + shortpath + '</span></td>\
								<td>' + ToSize(rdata.files[i].size) + '</td>\
								<td>' + getLocalTime(rdata.files[i].time) + '</td>\
								<td style="text-align: right;">\
									<a class="btlink" href="javascript:;" onclick="ReRecycleBin(\'' + rdata.files[i].rname.replace(/'/, "\\'") + '\',this)">' + lan.files.recycle_bin_re + '</a>\
									 | <a class="btlink" href="javascript:;" onclick="DelRecycleBin(\'' + rdata.files[i].rname.replace(/'/, "\\'") + '\',this)">' + lan.files.recycle_bin_del + '</a>\
								</td>\
							</tr>'
                }
                $("#RecycleBody").html(body);
                return;
                break;
            case 2:
                for (var i = 0; i < rdata.dirs.length; i++) {
                    var shortwebname = rdata.dirs[i].name.replace(/'/, "\\'");
                    var shortpath = rdata.dirs[i].dname;
                    if (shortwebname.length > 20) shortwebname = shortwebname.substring(0, 20) + "...";
                    if (shortpath.length > 20) shortpath = shortpath.substring(0, 20) + "...";
                    body += '<tr>\
								<td><span class=\'ico ico-folder\'></span><span class="tname" title="' + rdata.dirs[i].name + '">' + shortwebname + '</span></td>\
								<td><span title="' + rdata.dirs[i].dname + '">' + shortpath + '</span></td>\
								<td>' + ToSize(rdata.dirs[i].size) + '</td>\
								<td>' + getLocalTime(rdata.dirs[i].time) + '</td>\
								<td style="text-align: right;">\
									<a class="btlink" href="javascript:;" onclick="ReRecycleBin(\'' + rdata.dirs[i].rname.replace(/'/, "\\'") + '\',this)">' + lan.files.recycle_bin_re + '</a>\
									 | <a class="btlink" href="javascript:;" onclick="DelRecycleBin(\'' + rdata.dirs[i].rname.replace(/'/, "\\'") + '\',this)">' + lan.files.recycle_bin_del + '</a>\
								</td>\
							</tr>'
                }
                $("#RecycleBody").html(body);
                return;
                break;
            case 3:
                for (var i = 0; i < rdata.files.length; i++) {
                    if (rdata.files[i].name.indexOf('BTDB_') != -1) continue;
                    var shortwebname = rdata.files[i].name.replace(/'/, "\\'");
                    var shortpath = rdata.files[i].dname;
                    if (shortwebname.length > 20) shortwebname = shortwebname.substring(0, 20) + "...";
                    if (shortpath.length > 20) shortpath = shortpath.substring(0, 20) + "...";
                    body += '<tr>\
								<td><span class="ico ico-' + (GetExtName(rdata.files[i].name)) + '"></span><span class="tname" title="' + rdata.files[i].name + '">' + shortwebname + '</span></td>\
								<td><span title="' + rdata.files[i].dname + '">' + shortpath + '</span></td>\
								<td>' + ToSize(rdata.files[i].size) + '</td>\
								<td>' + getLocalTime(rdata.files[i].time) + '</td>\
								<td style="text-align: right;">\
									<a class="btlink" href="javascript:;" onclick="ReRecycleBin(\'' + rdata.files[i].rname.replace(/'/, "\\'") + '\',this)">' + lan.files.recycle_bin_re + '</a>\
									 | <a class="btlink" href="javascript:;" onclick="DelRecycleBin(\'' + rdata.files[i].rname.replace(/'/, "\\'") + '\',this)">' + lan.files.recycle_bin_del + '</a>\
								</td>\
							</tr>'
                }
                $("#RecycleBody").html(body);
                return;
                break;
            case 4:
                for (var i = 0; i < rdata.files.length; i++) {
                    if (ReisImage(getFileName(rdata.files[i].name))) {
                        var shortwebname = rdata.files[i].name.replace(/'/, "\\'");
                        var shortpath = rdata.files[i].dname;
                        if (shortwebname.length > 20) shortwebname = shortwebname.substring(0, 20) + "...";
                        if (shortpath.length > 20) shortpath = shortpath.substring(0, 20) + "...";
                        body += '<tr>\
								<td><span class="ico ico-' + (GetExtName(rdata.files[i].name)) + '"></span><span class="tname" title="' + rdata.files[i].name + '">' + shortwebname + '</span></td>\
								<td><span title="' + rdata.files[i].dname + '">' + shortpath + '</span></td>\
								<td>' + ToSize(rdata.files[i].size) + '</td>\
								<td>' + getLocalTime(rdata.files[i].time) + '</td>\
								<td style="text-align: right;">\
									<a class="btlink" href="javascript:;" onclick="ReRecycleBin(\'' + rdata.files[i].rname.replace(/'/, "\\'") + '\',this)">' + lan.files.recycle_bin_re + '</a>\
									 | <a class="btlink" href="javascript:;" onclick="DelRecycleBin(\'' + rdata.files[i].rname.replace(/'/, "\\'") + '\',this)">' + lan.files.recycle_bin_del + '</a>\
								</td>\
							</tr>'
                    }
                }
                $("#RecycleBody").html(body);
                return;
                break;
            case 5:
                for (var i = 0; i < rdata.files.length; i++) {
                    if (rdata.files[i].name.indexOf('BTDB_') != -1) continue;
                    if (!(ReisImage(getFileName(rdata.files[i].name)))) {
                        var shortwebname = rdata.files[i].name.replace(/'/, "\\'");
                        var shortpath = rdata.files[i].dname;
                        if (shortwebname.length > 20) shortwebname = shortwebname.substring(0, 20) + "...";
                        if (shortpath.length > 20) shortpath = shortpath.substring(0, 20) + "...";
                        body += '<tr>\
								<td><span class="ico ico-' + (GetExtName(rdata.files[i].name)) + '"></span><span class="tname" title="' + rdata.files[i].name + '">' + shortwebname + '</span></td>\
								<td><span title="' + rdata.files[i].dname + '">' + shortpath + '</span></td>\
								<td>' + ToSize(rdata.files[i].size) + '</td>\
								<td>' + getLocalTime(rdata.files[i].time) + '</td>\
								<td style="text-align: right;">\
									<a class="btlink" href="javascript:;" onclick="ReRecycleBin(\'' + rdata.files[i].rname.replace(/'/, "\\'") + '\',this)">' + lan.files.recycle_bin_re + '</a>\
									 | <a class="btlink" href="javascript:;" onclick="DelRecycleBin(\'' + rdata.files[i].rname.replace(/'/, "\\'") + '\',this)">' + lan.files.recycle_bin_del + '</a>\
								</td>\
							</tr>'
                    }
                }
                $("#RecycleBody").html(body);
                return;
            case 6:
                for (var i = 0; i < rdata.files.length; i++) {
                    if (rdata.files[i].name.indexOf('BTDB_') != -1) {
                        var shortwebname = rdata.files[i].name.replace(/'/, "\\'");
                        var shortpath = rdata.files[i].dname;
                        if (shortwebname.length > 20) shortwebname = shortwebname.substring(0, 20) + "...";
                        if (shortpath.length > 20) shortpath = shortpath.substring(0, 20) + "...";
                        body += '<tr>\
								<td><span class="ico ico-' + (GetExtName(rdata.files[i].name)) + '"></span><span class="tname" title="' + rdata.files[i].name + '">' + shortwebname.replace('BTDB_', '') + '</span></td>\
								<td><span title="' + rdata.files[i].dname + '">mysql://' + shortpath.replace('BTDB_', '') + '</span></td>\
								<td>-</td>\
								<td>' + getLocalTime(rdata.files[i].time) + '</td>\
								<td style="text-align: right;">\
									<a class="btlink" href="javascript:;" onclick="ReRecycleBin(\'' + rdata.files[i].rname.replace(/'/, "\\'") + '\',this)">' + lan.files.recycle_bin_re + '</a>\
									 | <a class="btlink" href="javascript:;" onclick="DelRecycleBin(\'' + rdata.files[i].rname.replace(/'/, "\\'") + '\',this)">' + lan.files.recycle_bin_del + '</a>\
								</td>\
							</tr>'
                    }
                }
                $("#RecycleBody").html(body);
                return;
                break;
        }


        var tablehtml = '<div class="re-head">\
				<div style="margin-left: 3px;" class="ss-text">\
                        <em>' + lan.files.recycle_bin_on + '</em>\
                        <div class="ssh-item">\
                                <input class="btswitch btswitch-ios" id="Set_Recycle_bin" type="checkbox" ' + (rdata.status ? 'checked' : '') + '>\
                                <label class="btswitch-btn" for="Set_Recycle_bin" onclick="Set_Recycle_bin()"></label>\
                        </div>\
                        <em style="margin-left: 20px;">' + lan.files.recycle_bin_on_db + '</em>\
                        <div class="ssh-item">\
                                <input class="btswitch btswitch-ios" id="Set_Recycle_bin_db" type="checkbox" ' + (rdata.status_db ? 'checked' : '') + '>\
                                <label class="btswitch-btn" for="Set_Recycle_bin_db" onclick="Set_Recycle_bin(1)"></label>\
                        </div>\
                </div>\
				<span style="line-height: 32px; margin-left: 30px;">' + lan.files.recycle_bin_ps + '</span>\
                <button style="float: right" class="btn btn-default btn-sm" onclick="CloseRecycleBin();">' + lan.files.recycle_bin_close + '</button>\
				</div>\
				<div class="re-con">\
					<div class="re-con-menu">\
						<p class="on" onclick="Recycle_bin(1)">' + lan.files.recycle_bin_type1 + '</p>\
						<p onclick="Recycle_bin(2)">' + lan.files.recycle_bin_type2 + '</p>\
						<p onclick="Recycle_bin(3)">' + lan.files.recycle_bin_type3 + '</p>\
						<p onclick="Recycle_bin(4)">' + lan.files.recycle_bin_type4 + '</p>\
						<p onclick="Recycle_bin(5)">' + lan.files.recycle_bin_type5 + '</p>\
						<p onclick="Recycle_bin(6)">' + lan.files.recycle_bin_type6 + '</p>\
					</div>\
					<div class="re-con-con">\
					<div style="margin: 15px;" class="divtable">\
					<table width="100%" class="table table-hover">\
						<thead>\
							<tr>\
								<th>' + lan.files.recycle_bin_th1 + '</th>\
								<th>' + lan.files.recycle_bin_th2 + '</th>\
								<th>' + lan.files.recycle_bin_th3 + '</th>\
								<th width="150">' + lan.files.recycle_bin_th4 + '</th>\
								<th style="text-align: right;" width="110">' + lan.files.recycle_bin_th5 + '</th>\
							</tr>\
						</thead>\
					<tbody id="RecycleBody" class="list-list">' + body + '</tbody>\
			</table></div></div></div>';
        if (type == "open") {
            layer.open({
                type: 1,
                shift: 5,
                closeBtn: 2,
                area: ['80%', '606px'],
                title: lan.files.recycle_bin_title,
                content: tablehtml
            });

            if (window.location.href.indexOf("database") != -1) {
                Recycle_bin(6);
                $(".re-con-menu p:last-child").addClass("on").siblings().removeClass("on");
            } else {
                Recycle_bin(1);
            }
        }
        $(".re-con-menu p").click(function () {
            $(this).addClass("on").siblings().removeClass("on");
        })
    });
}

function getFileName(name) {
    var text = name.split(".");
    var n = text.length - 1;
    text = text[n];
    return text;
}

function ReisImage(fileName) {
    var exts = ['jpg', 'jpeg', 'png', 'bmp', 'gif', 'tiff', 'ico'];
    for (var i = 0; i < exts.length; i++) {
        if (fileName == exts[i]) return true
    }
    return false;
}

function ReRecycleBin(path, obj) {
    layer.confirm(lan.files.recycle_bin_re_msg, {
        title: lan.files.recycle_bin_re_title,
        closeBtn: 2,
        icon: 3
    }, function () {
        var loadT = layer.msg(lan.files.recycle_bin_re_the, {
            icon: 16,
            time: 0,
            shade: [0.3, '#000']
        });
        $.post('/files?action=Re_Recycle_bin', 'path=' + encodeURIComponent(path), function (rdata) {
            layer.close(loadT);
            layer.msg(rdata.msg, {
                icon: rdata.status ? 1 : 5
            });
            $(obj).parents('tr').remove();
        });
    });
}

function DelRecycleBin(path, obj) {
    layer.confirm(lan.files.recycle_bin_del_msg, {
        title: lan.files.recycle_bin_del_title,
        closeBtn: 2,
        icon: 3
    }, function () {
        var loadT = layer.msg(lan.files.recycle_bin_del_the, {
            icon: 16,
            time: 0,
            shade: [0.3, '#000']
        });
        $.post('/files?action=Del_Recycle_bin', 'path=' + encodeURIComponent(path), function (rdata) {
            layer.close(loadT);
            layer.msg(rdata.msg, {
                icon: rdata.status ? 1 : 5
            });
            $(obj).parents('tr').remove();
        });
    });
}

function CloseRecycleBin() {
    layer.confirm(lan.files.recycle_bin_close_msg, {
        title: lan.files.recycle_bin_close,
        closeBtn: 2,
        icon: 3
    }, function () {
        var loadT = layer.msg("<div class='myspeed'>" + lan.files.recycle_bin_close_the + "</div>", {
            icon: 16,
            time: 0,
            shade: [0.3, '#000']
        });
        setTimeout(function () {
            getSpeed('.myspeed');
        }, 1000);
        $.post('/files?action=Close_Recycle_bin', '', function (rdata) {
            layer.close(loadT);
            layer.msg(rdata.msg, {
                icon: rdata.status ? 1 : 5
            });
            $("#RecycleBody").html('');
        });
    });
}

function Set_Recycle_bin(db) {
    var loadT = layer.msg(lan.public.the, {
        icon: 16,
        time: 0,
        shade: [0.3, '#000']
    });
    var data = {}
    if (db == 1) {
        data = {
            db: db
        };
    }
    $.post('/files?action=Recycle_bin', data, function (rdata) {
        layer.close(loadT);
        layer.msg(rdata.msg, {
            icon: rdata.status ? 1 : 5
        });
    });
}

function get_path_size(path) {
    var loadT = layer.msg(lan.files.calc_size, {
        icon: 16,
        time: 0,
        shade: [0.3, '#000']
    });
    $.post('/files?action=get_path_size', {
        path: path
    }, function (rdata) {
        layer.close(loadT);
        var myclass = '.' + rdata.path.replace(/[^\w]/g, '-');
        console.log(myclass)
        console.log($(myclass).text())
        $(myclass).text(ToSize(rdata.size));
    });
}


function path_check(path) {
    if (path == '/') return path;
    path = path.replace(/[\/]{2,}/g, '/');
    path = path.replace(/[\/]+$/g, '');
    return path;
}

function GetFiles(Path, sort) {
    var searchtype = Path;
    var p = '1';
    if (!isNaN(Path)) {
        p = Path;
        Path = getCookie('Path');
    }

    Path = path_check(Path);

    var data = {};
    var search = '';
    var searchV = $("#SearchValue").val();
    if (searchV.length > 0 && searchtype == "1") {
        data['search'] = searchV;
        if ($("#search_all")[0].checked) {
            data['all'] = 'True'
        }
    }

    var old_scroll_top = 0;
    if (getCookie('Path') === Path) {
        old_scroll_top = $(".oldTable").scrollTop();
    }

    var sorted = '';
    var reverse = '';
    if (!sort) {
        sort = getCookie('files_sort');
        reverse = getCookie(sort + '_reverse');
    } else {
        reverse = getCookie(sort + '_reverse');
        if (reverse === 'True') {
            reverse = 'False';
        } else {
            reverse = 'True';
        }
    }
    if (sort) {
        data['sort'] = sort;
        data['reverse'] = reverse;
        setCookie(sort + '_reverse', reverse);
        setCookie('files_sort', sort);
    }


    var showRow = getCookie('showRow');
    if (!showRow) showRow = '200';
    var Body = '';
    data['path'] = Path;


    if (searchV) {
        var loadT = layer.msg(lan.files.search_now, {
            icon: 16,
            time: 0,
            shade: [0.3, '#000']
        });
    }
    var totalSize = 0;
    $.post('/files?action=GetDir&tojs=GetFiles&p=' + p + '&showRow=' + showRow + search, data, function (rdata) {
        if (searchV) layer.close(loadT);
        if (rdata.status === false) {
            layer.msg(rdata.msg, {
                icon: 2
            });
            return;
        }

        var rows = ['10', '50', '100', '200', '500', '1000', '2000'];
        var rowOption = '';
        for (var i = 0; i < rows.length; i++) {
            var rowSelected = '';
            if (showRow == rows[i]) rowSelected = 'selected';
            rowOption += '<option value="' + rows[i] + '" ' + rowSelected + '>' + rows[i] + '</option>';
        }

        $("#filePage").html(rdata.PAGE);
        $("#filePage div").append("<span class='Pcount-item'>" + lan.files.per_page + "<select style='margin-left: 3px;margin-right: 3px;border:#ddd 1px solid' class='showRow'>" + rowOption + "</select>" + lan.files.piece + "</span>");
        $("#filePage .Pcount").css("left", "16px");
        if (rdata.DIR == null) rdata.DIR = [];
        for (var i = 0; i < rdata.DIR.length; i++) {
            var fmp = rdata.DIR[i].split(";");
            var cnametext = fmp[0] + fmp[5];
            fmp[0] = fmp[0].replace(/'/, "\\'");
            if (cnametext.length > 20) {
                cnametext = cnametext.substring(0, 20) + '...'
            }
            if (isChineseChar(cnametext)) {
                if (cnametext.length > 10) {
                    cnametext = cnametext.substring(0, 10) + '...'
                }
            }
            var fileMsg = '';
            if (fmp[0].indexOf('Recycle_bin') != -1) {
                fileMsg = 'PS: Recycle Bin directory, Do not operate';
            }
            if (fileMsg != '') {
                fileMsg = '<span style="margin-left: 30px; color: #999;">' + fileMsg + '</span>';
            }
            var timetext = '--';
            //<a class='btlink' href='javascript:;' onclick=\"webshell_dir('" + rdata.PATH + "/" + fmp[0] + "')\">" + lan.files.dir_menu_webshell + "</a> |---在<td class='editmenu'><span>下一行的
            if (getCookie("rank") == "a") {
                $("#set_list").addClass("active");
                $("#set_icon").removeClass("active");
                if (rdata.PATH=='/') rdata.PATH = '';
                Body += "<tr class='folderBoxTr' fileshare='"+ fmp[6] +"' data-composer='"+fmp[7]+"' data-path='" + rdata.PATH + "/" + fmp[0] + "' filetype='dir'>\
						<td><input type='checkbox' name='id' value='" + fmp[0] + "'></td>\
						<td class='column-name'><span class='cursor' onclick=\"GetFiles('" + rdata.PATH + "/" + fmp[0] + "')\"><span class='ico ico-folder'></span><a class='text' title='" + fmp[0] + fmp[5] + "'>" + cnametext + fileMsg + "</a></span></td>\
						<td><a class='btlink " + (rdata.PATH + '/' + fmp[0]).replace(/[^\w]/g, '-') + "' onclick=\"get_path_size('" + rdata.PATH + "/" + fmp[0] + "')\">" + lan.files.calc_click + "</a></td>\
						<td>" + getLocalTime(fmp[2]) + "</td>\
						<td>" + fmp[3] + "</td>\
						<td>" + fmp[4] + "</td>\
						<td class='editmenu'><span>\
						<a class='btlink' href='javascript:;' onclick=\"CopyFile('" + rdata.PATH + "/" + fmp[0] + "')\">" + lan.files.file_menu_copy + "</a> | \
						<a class='btlink' href='javascript:;' onclick=\"CutFile('" + rdata.PATH + "/" + fmp[0] + "')\">" + lan.files.file_menu_mv + "</a> | \
						<a class='btlink' href=\"javascript:ReName(0,'" + fmp[0] + "');\">" + lan.files.file_menu_rename + "</a> | \
						<a class='btlink' href=\"javascript:SetChmod(0,'" + rdata.PATH + "/" + fmp[0] + "',1);\">" + lan.files.file_menu_auth + "</a> | \
						<a class='btlink' href=\"javascript:Zip('" + rdata.PATH + "/" + fmp[0] + "');\">" + lan.files.file_menu_zip + "</a> | \
						<a class='btlink' href='javascript:;' onclick=\"DeleteDir('" + rdata.PATH + "/" + fmp[0] + "')\">" + lan.files.file_menu_del + "</a></span>\
					</td></tr>";
            } else {
                $("#set_icon").addClass("active");
                $("#set_list").removeClass("active");
                Body += "<div class='file folderBox menufolder' fileshare='"+ fmp[6] +"' data-path='" + rdata.PATH + "/" + fmp[0] + "' filetype='dir' title='" + lan.files.file_name + "：" + fmp[0] + "&#13;" + lan.files.file_size + "：" + ToSize(fmp[1]) + "&#13;" + lan.files.file_etime + "：" + getLocalTime(fmp[2]) + "&#13;" + lan.files.file_auth + "：" + fmp[3] + "&#13;" + lan.files.file_own + "：" + fmp[4] + "'>\
						<input type='checkbox' name='id' value='" + fmp[0] + "'>\
						<div class='ico ico-folder' ondblclick=\"GetFiles('" + rdata.PATH + "/" + fmp[0] + "')\"></div>\
						<div class='titleBox' onclick=\"GetFiles('" + rdata.PATH + "/" + fmp[0] + "')\"><span class='tname'>" + fmp[0] + "</span></div>\
						</div>";
            }
        }
        for (var i = 0; i < rdata.FILES.length; i++) {
            if (rdata.FILES[i] == null) continue;
            var fmp = rdata.FILES[i].split(";");
            var displayZip = isZip(fmp[0]);
            var bodyZip = '';
            var download = '';
            var file_webshell = '';
            var cnametext = fmp[0] + fmp[5];
            fmp[0] = fmp[0].replace(/'/, "\\'");
            if (cnametext.length > 48) {
                cnametext = cnametext.substring(0, 48) + '...'
            }
            if (isChineseChar(cnametext)) {
                if (cnametext.length > 16) {
                    cnametext = cnametext.substring(0, 16) + '...'
                }
            }
            if (isPhp(fmp[0])) {
                file_webshell = "<a class='btlink' href='javascript:;' onclick=\"php_file_webshell('" + rdata.PATH + "/" + fmp[0] + "')\">" + lan.files.file_menu_webshell + "</a> | ";
            }
            if (displayZip != -1) {
                bodyZip = "<a class='btlink' href='javascript:;' onclick=\"UnZip('" + rdata.PATH + "/" + fmp[0] + "'," + displayZip + ")\">" + lan.files.file_menu_unzip + "</a> | ";
            }
            if (isText(fmp[0])) {
                bodyZip = "<a class='btlink' href='javascript:;' onclick=\"openEditorView(0,'" + rdata.PATH + "/" + fmp[0] + "')\">" + lan.files.file_menu_edit + "</a> | ";
            }
            if (isVideo(fmp[0])) {
                bodyZip = "<a class='btlink' href='javascript:;' onclick=\"GetPlay('" + rdata.PATH + "/" + fmp[0] + "')\">Play</a> | ";
            }
            if (isImage(fmp[0])) {
                download = "<a class='btlink' href='javascript:;' onclick=\"GetImage('" + rdata.PATH + "/" + fmp[0] + "')\">" + lan.files.file_menu_img + "</a> | ";
            } else {
                download = "<a class='btlink' href='javascript:;' onclick=\"GetFileBytes('" + rdata.PATH + "/" + fmp[0] + "'," + fmp[1] + ")\">" + lan.files.file_menu_down + "</a> | ";
            }

            totalSize += parseInt(fmp[1]);
            if (getCookie("rank") == "a") {
                var fileMsg = '';
                switch (fmp[0]) {
                    case '.user.ini':
                        fileMsg = lan.files.ps_php;
                        break;
                    case '.htaccess':
                        fileMsg = lan.files.ps_ap;
                        break;
                    case 'swap':
                        fileMsg = lan.files.ps_swap;
                        break;
                }

                if (fmp[0].indexOf('.upload.tmp') != -1) {
                    fileMsg = lan.files.upload_files_tips1;
                }

                if (fileMsg != '') {
                    fileMsg = '<span style="margin-left: 30px; color: #999;">' + fileMsg + '</span>';
                }
                Body += "<tr class='folderBoxTr' fileshare='" + fmp[6] + "' data-path='" + rdata.PATH + "/" + fmp[0] + "' filetype='" + fmp[0] + "'><td><input type='checkbox' name='id' value='" + fmp[0] + "'></td>\
						<td class='column-name'><span class='ico ico-" + (GetExtName(fmp[0])) + "'></span><a class='text' title='" + fmp[0] + fmp[5] + "'>" + cnametext + fileMsg + "</a></td>\
						<td>" + (ToSize(fmp[1])) + "</td>\
						<td>" + ((fmp[2].length > 11) ? fmp[2] : getLocalTime(fmp[2])) + "</td>\
						<td>" + fmp[3] + "</td>\
						<td>" + fmp[4] + "</td>\
						<td class='editmenu'>\
						<span><a class='btlink' href='javascript:;' onclick=\"CopyFile('" + rdata.PATH + "/" + fmp[0] + "')\">" + lan.files.file_menu_copy + "</a> | \
						<a class='btlink' href='javascript:;' onclick=\"CutFile('" + rdata.PATH + "/" + fmp[0] + "')\">" + lan.files.file_menu_mv + "</a> | \
						<a class='btlink' href='javascript:;' onclick=\"ReName(0,'" + fmp[0] + "')\">" + lan.files.file_menu_rename + "</a> | \
						<a class='btlink' href=\"javascript:SetChmod(0,'" + rdata.PATH + "/" + fmp[0] + "',0);\">" + lan.files.file_menu_auth + "</a> | \
						<a class='btlink' href=\"javascript:Zip('" + rdata.PATH + "/" + fmp[0] + "');\">" + lan.files.file_menu_zip + "</a> | \
						" + bodyZip + download + "\
						<a class='btlink' href='javascript:;' onclick=\"DeleteFile('" + rdata.PATH + "/" + fmp[0] + "')\">" + lan.files.file_menu_del + "</a>\
						</span></td></tr>";
            } else {
                Body += "<div class='file folderBox menufile' fileshare='"+ fmp[6] +"' data-path='" + rdata.PATH + "/" + fmp[0] + "' filetype='" + fmp[0] + "' title='" + lan.files.file_name + "：" + fmp[0] + "&#13;" + lan.files.file_size + "：" + ToSize(fmp[1]) + "&#13;" + lan.files.file_etime + "：" + getLocalTime(fmp[2]) + "&#13;" + lan.files.file_auth + "：" + fmp[3] + "&#13;" + lan.files.file_own + "：" + fmp[4] + "'>\
						<input type='checkbox' name='id' value='" + fmp[0] + "'>\
						<div class='ico ico-" + (GetExtName(fmp[0])) + "'></div>\
						<div class='titleBox'><span class='tname'>" + fmp[0] + "</span></div>\
						</div>";
            }
        }
        var dirInfo = '(' + lan.files.get_size.replace('{1}', rdata.DIR.length + '').replace('{2}', rdata.FILES.length + '') + '<font id="pathSize"><a class="btlink ml5" onClick="GetPathSize()">' + lan.files.get + '</a></font>)';
        $("#DirInfo").html(dirInfo);
        if (getCookie("rank") === "a") {
            var sort_icon = '<span data-id="status" class="glyphicon glyphicon-triangle-' + ((data['reverse'] !== 'False') ? 'bottom' : 'top') + '" style="margin-left:5px;color:#bbb"></span>';
            var tablehtml = '<div class="newTable"><table width="100%" border="0" cellpadding="0" cellspacing="0" class="table table-hover">\
                              <thead>\
                                  <tr>\
                                      <th width="30"><input type="checkbox" id="setBox" placeholder=""></th>\
                                      <th><a style="cursor: pointer;" onclick="GetFiles(' + p + ',\'name\')">' + lan.files.file_name + ((data['sort'] === 'name' || !data['sort']) ? sort_icon : '') + '</a></th>\
                                      <th><a style="cursor: pointer;" onclick="GetFiles(' + p + ',\'size\')">' + lan.files.file_size + ((data['sort'] === 'size') ? sort_icon : '') + '</a></th>\
                                      <th><a style="cursor: pointer;" onclick="GetFiles(' + p + ',\'mtime\')">' + lan.files.file_etime + ((data['sort'] === 'mtime') ? sort_icon : '') + '</a></th>\
                                      <th><a style="cursor: pointer;" onclick="GetFiles(' + p + ',\'accept\')">' + lan.files.file_auth + ((data['sort'] === 'accept') ? sort_icon : '') + '</a></th>\
                                      <th><a style="cursor: pointer;" onclick="GetFiles(' + p + ',\'user\')">' + lan.files.file_own + ((data['sort'] === 'user') ? sort_icon : '') + '</a></th>\
                                      <th style="text-align: right;" width="330">' + lan.files.file_act + '</th>\
									  <th></th>\
                                  </tr>\
                              </thead>\
                              </table>\
							</div>\
							<div class="newTableShadow"></div>\
            				<div class="oldTable" style="overflow: auto;height: 500px;margin-top: -8px;"><table width="100%" border="0" cellpadding="0" cellspacing="0" class="table table-hover">\
							<thead>\
								<tr>\
									<th width="30"><input type="checkbox" id="setBox" placeholder=""></th>\
									<th><a style="cursor: pointer;" class="btlink" onclick="GetFiles(' + p + ',\'name\')">' + lan.files.file_name + ((data['sort'] === 'name' || !data['sort']) ? sort_icon : '') + '</a></th>\
									<th><a style="cursor: pointer;display: inline-block;min-width: 58px;" class="btlink" onclick="GetFiles(' + p + ',\'size\')">' + lan.files.file_size + ((data['sort'] === 'size') ? sort_icon : '') + '</a></th>\
									<th><a style="cursor: pointer;" class="btlink minText" onclick="GetFiles(' + p + ',\'mtime\')">' + lan.files.file_etime + ((data['sort'] === 'mtime') ? sort_icon : '') + '</a></th>\
									<th><a style="cursor: pointer;" class="btlink minText" onclick="GetFiles(' + p + ',\'accept\')">' + lan.files.file_auth + ((data['sort'] === 'accept') ? sort_icon : '') + '</a></th>\
									<th><a style="cursor: pointer;" class="btlink minText" onclick="GetFiles(' + p + ',\'user\')">' + lan.files.file_own + ((data['sort'] === 'user') ? sort_icon : '') + '</a></th>\
									<th style="text-align: right;" width="430">' + lan.files.file_act + '</th>\
								</tr>\
							</thead>\
							<tbody id="filesBody" class="list-list">' + Body + '</tbody>\
						</table></div><div class="oldTableShadow"></div>';
            $("#fileCon").removeClass("fileList").html(tablehtml);
            $("#tipTools").width($("#fileCon")[0].clientWidth - 30);
        } else {
            $("#fileCon").addClass("fileList").html(Body);
            $("#tipTools").width($("#fileCon")[0].clientWidth - 30);
        }
        $("#DirPathPlace input").val(rdata.PATH);
        var BarTools = '<div class="btn-group">\
						<button class="btn btn-default btn-sm dropdown-toggle" type="button" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">\
						' + lan.files.new + ' <span class="caret"></span>\
						</button>\
						<ul class="dropdown-menu">\
						<li><a href="javascript:CreateFile(0,\'' + Path + '\');">' + lan.files.new_empty_file + '</a></li>\
						<li><a href="javascript:CreateDir(0,\'' + Path + '\');">' + lan.files.new_dir + '</a></li>\
						</ul>\
						</div>';
        if (rdata.PATH != '/') {
            BarTools += ' <button onclick="javascript:BackDir();" class="btn btn-default btn-sm glyphicon glyphicon-arrow-left" title="' + lan.files.return+'"></button>';
        }
        setCookie('Path', rdata.PATH);
        BarTools += ' <button onclick="javascript:GetFiles(\'' + rdata.PATH + '\');" class="btn btn-default btn-sm glyphicon glyphicon-refresh" title="' + lan.public.fresh + '"></button> <button onclick="web_shell()" title="' + lan.files.shell + '" type="button" class="btn btn-default btn-sm"><em class="ico-cmd"></em></button><button onclick="get_download_url_list()" type="button" class="btn btn-default btn-sm ml5">Share List</button>';


        //收藏夹
        var shtml = '<div class="btn-group">\
						<button style="margin-left: 5px;" class="btn btn-default btn-sm dropdown-toggle" type="button" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">Favorites <span class="caret"></span>\
						</button>\
						<ul class="dropdown-menu">'

        for (var i = 0; i < rdata.STORE.length; i++) {
            shtml += '<li class="file-types" title="' + rdata.STORE[i].path + '"><div style="width:200px"><span class="ico ' + (rdata.STORE[i].type === 'file' ? 'ico-file' : 'ico-folder') + '"></span><a href="javascript:;"  style="display: inline-block;width:150px;overflow: hidden;text-overflow: ellipsis;vertical-align: top;white-space: nowrap;" onclick="' + (rdata.STORE[i].type === 'file' ? 'openEditorView(0,\'' + rdata.STORE[i].path + '\')' : 'GetFiles(\'' + rdata.STORE[i].path + '\')') + '">' + rdata.STORE[i].name + '</a></div>';
        }
        shtml += '<li style="text-align: center;"><a href="javascript: ;" onclick="set_file_store(\'' + rdata.PATH + '\')">+ Management</a></li></ul></div>'

        BarTools += shtml;

        var copyName = getCookie('copyFileName');
        var cutName = getCookie('cutFileName');
        var isPaste = (copyName == 'null') ? cutName : copyName;
        if (isPaste != 'null' && isPaste != undefined) {
            BarTools += ' <button onclick="javascript:PasteFile(\'' + (GetFileName(isPaste)) + '\');" class="btn btn-default btn-Warning btn-sm">' + lan.files.paste + '</button>';
        }

        $("#Batch").html('');
        var BatchTools = '';
        var isBatch = getCookie('BatchSelected');
        if (isBatch == 1 || isBatch == '1') {
            BatchTools += ' <button onclick="javascript:BatchPaste();" class="btn btn-default btn-sm">' + lan.files.paste_all + '</button>';
        }
        $("#Batch").html(BatchTools);
        $("#setBox").prop("checked", false);

        $("#BarTools").html(BarTools);
        $(".oldTable").scrollTop(old_scroll_top);
        $("input[name=id]").click(function () {
            if ($(this).prop("checked")) {
                $(this).prop("checked", true);
                $(this).parents("tr").addClass("ui-selected");
            } else {
                $(this).prop("checked", false);
                $(this).parents("tr").removeClass("ui-selected");
            }
            showSeclect()
        });

        // // 鼠标移入移出事件
        // $('.file-types').hover(function () {
        //     // 鼠标移入时添加hover类
        //     $('.dropdown-menu-li').hide();
        //     $(this).find('.dropdown-menu-li').show();

        // }, function () {
        //     $('.dropdown-menu-li').hide();
        //     // 鼠标移出时移出hover类

        // });

        $("#setBox").click(function () {
            if ($(this).prop("checked")) {
                $("input[name=id]").prop("checked", true);
                $("#filesBody > tr").addClass("ui-selected");

            } else {
                $("input[name=id]").prop("checked", false);
                $("#filesBody > tr").removeClass("ui-selected");
            }
            showSeclect();
        });

        $("#filesBody .btlink").click(function (e) {
            e.stopPropagation();
        });
        $("input[name=id]").dblclick(function (e) {
            e.stopPropagation();
        });
        $("#filesBody").bind("contextmenu", function (e) {
            return false;
        });
        bindselect();
        $("#filesBody").mousedown(function (e) {
            var count = totalFile();
            if (e.which == 3) {
                if (count > 1) {
                    RClickAll(e);
                } else {
                    return
                }
            }
        });
        $(".folderBox,.folderBoxTr").mousedown(function (e) {
            var count = totalFile();
            if (e.which == 3) {
                if (count <= 1) {
                    var a = $(this);
                    a.contextify(RClick(a.attr("filetype"), a.attr("data-path"), a.find("input").val(), rdata,a.attr('fileshare'),a.attr('data-composer')));
                    $(this).find('input').prop("checked", true);
                    $(this).addClass('ui-selected');
                    $(this).siblings().removeClass('ui-selected').find('input').prop("checked", false);
                }
                else {
                    RClickAll(e);
                }
            }
        });
        $(".showRow").change(function () {
            setCookie('showRow', $(this).val());
            GetFiles(p);
        });
        PathPlaceBtn(rdata.PATH);
        auto_table_width();
    });
}

function webshell_dir(path) {
    layer.confirm('Directory scan will include php files in subdirectories, whether to operate？', {
        title: lan.files.dir_menu_webshell,
        closeBtn: 2,
        icon: 3
    }, function (index) {
        layer.msg(lan.public.the, {
            icon: 16,
            time: 0,
            shade: [0.3, '#000']
        });
        $.post('/files?action=dir_webshell_check', 'path=' + path, function (rdata) {
            layer.close(index);
            layer.msg(rdata.msg, {
                icon: rdata.status ? 1 : 2
            });
        });
    });
}

function php_file_webshell(file) {
    var loadT = layer.msg('Scanning files, please wait ...', {
        icon: 16,
        time: 0,
        shade: [0.3, '#000']
    });
    $.post('/files?action=file_webshell_check', 'filename=' + file, function (rdata) {
        layer.close(loadT);
        layer.msg(rdata.msg, {
            icon: rdata.status ? 1 : 2
        });
    })
}

function auto_table_width() {
    var oldTable = $(window).height() - $('#tipTools')[0].getBoundingClientRect().height - $('#filePage')[0].getBoundingClientRect().height - $('.footer')[0].getBoundingClientRect().height - 111;
    var oldTable_heigth = $('.oldTable table').height();
    $('.oldTable thead th').each(function (index, el) {
        var table_th = $('.oldTable thead th').length;
        $('.newTable thead th').eq(index).attr('width', el.offsetWidth);
        if (index == (table_th - 1)) $('.newTable thead th').eq(table_th).attr('width', '10').css('padding', '0');
    });
    if (oldTable_heigth > oldTable) {
        $('.oldTableShadow,.newTableShadow').show();
        $('.oldTable').css('marginTop', '0')
    } else {
        $('.oldTableShadow,.newTableShadow').hide();
        $('.oldTable').css('marginTop', '0')
    }
    $('.oldTable').height(oldTable);
    $('.oldTable table').css({
        'marginTop': '-36px'
    })

}


function totalFile() {
    var el = $("input[name='id']");
    var len = el.length;
    var count = 0;
    for (var i = 0; i < len; i++) {
        if (el[i].checked == true) {
            count++;
        }
    }
    return count;
}

function bindselect() {
    $("#filesBody").selectable({
        autoRefresh: false,
        filter: "tr,.folderBox",
        cancel: "a,span,input,.ico-folder",
        selecting: function (e) {
            $(".ui-selecting").find("input").prop("checked", true);
            showSeclect();
        },
        selected: function (e) {
            $(".ui-selectee").find("input").prop("checked", false);
            $(".ui-selected", this).each(function () {
                $(this).find("input").prop("checked", true);
                showSeclect();
            });
        },
        unselecting: function (e) {
            $(".ui-selectee").find("input").prop("checked", false);
            $(".ui-selecting").find("input").prop("checked", true);
            showSeclect();
            $("#rmenu").hide()
        }
    });
    $("#filesBody").selectable("refresh");
    $(".ico-folder").click(function () {
        $(this).parent().addClass("ui-selected").siblings().removeClass("ui-selected");
        $(".ui-selectee").find("input").prop("checked", false);
        $(this).prev("input").prop("checked", true);
        showSeclect();
    })
}

function showSeclect() {
    var count = totalFile();
    var BatchTools = '';
    if (count > 1) {
        BatchTools = '<button onclick="javascript:Batch(1);" class="btn btn-default btn-sm">' + lan.files.file_menu_copy + '</button>\
						  <button onclick="javascript:Batch(2);" class="btn btn-default btn-sm">' + lan.files.file_menu_mv + '</button>\
						  <button onclick="javascript:Batch(3);" class="btn btn-default btn-sm">' + lan.files.file_menu_auth + '</button>\
						  <button onclick="javascript:Batch(5);" class="btn btn-default btn-sm">' + lan.files.file_menu_zip + '</button>\
						  <button onclick="javascript:Batch(4);" class="btn btn-default btn-sm">' + lan.files.file_menu_del + '</button>'
        $("#Batch").html(BatchTools);
    } else {
        $("#Batch").html(BatchTools);
    }
}
$("#tipTools").width($(".file-box")[0].clientWidth - 30);
$("#PathPlaceBtn").width($(".file-box").width() - 700);
$("#DirPathPlace input").width($(".file-box").width() - 700);
if ($(window).width() < 1160) {
    $("#PathPlaceBtn").width(290);
}
window.onresize = function () {
    $("#tipTools").width($(".file-box")[0].clientWidth - 30);
    $("#PathPlaceBtn").width($(".file-box").width() - 700);
    $("#DirPathPlace input").width($(".file-box").width() - 700);
    if ($(window).width() < 1160) {
        $("#PathPlaceBtn,#DirPathPlace input").width(290);
    }
    PathLeft();
    IsDiskWidth()
    auto_table_width();
}

function Batch(type, access) {
    var path = $("#DirPathPlace input").val();
    var el = document.getElementsByTagName('input');
    var len = el.length;
    var data = 'path=' + path + '&type=' + type;
    var name = 'data';
    var datas = []

    var oldType = getCookie('BatchPaste');

    for (var i = 0; i < len; i++) {
        if (el[i].checked == true && el[i].value != 'on') {
            datas.push(el[i].value)
        }
    }

    data += "&data=" + encodeURIComponent(JSON.stringify(datas))

    if (type == 3 && access == undefined) {
        SetChmod(0, lan.files.all);
        return;
    }

    if (type < 3) setCookie('BatchSelected', '1');
    setCookie('BatchPaste', type);

    if (access == 1) {
        var access = $("#access").val();
        var chown = $("#chown").val();
        var all = $("#accept_all").prop("checked") ? 'True' : 'False';
        data += '&access=' + access + '&user=' + chown + "&all=" + all;
        layer.closeAll();
    }
    if (type == 4) {
        AllDeleteFileSub(data, path);
        setCookie('BatchPaste', oldType);
        return;
    }

    if (type == 5) {
        var names = '';
        for (var i = 0; i < len; i++) {
            if (el[i].checked == true && el[i].value != 'on') {
                names += el[i].value + ',';
            }
        }
        Zip(names);
        return;
    }
    if (type == 6) {
        webshell_dir()
    }

    myloadT = layer.msg("<div class='myspeed'>" + lan.public.the + "</div>", {
        icon: 16,
        time: 0,
        shade: [0.3, '#000']
    });
    setTimeout(function () {
        getSpeed('.myspeed');
    }, 1000);
    $.post('/files?action=SetBatchData', data, function (rdata) {
        layer.close(myloadT);
        GetFiles(path);
        layer.msg(rdata.msg, {
            icon: 1
        });
    });
}

function BatchPaste() {
    var path = $("#DirPathPlace input").val();
    var type = getCookie('BatchPaste');
    var data = 'type=' + type + '&path=' + path;

    $.post('/files?action=CheckExistsFiles', {
        dfile: path
    }, function (result) {
        if (result.length > 0) {
            var tbody = '';
            for (var i = 0; i < result.length; i++) {
                tbody += '<tr><td>' + result[i].filename + '</td><td>' + ToSize(result[i].size) + '</td><td>' + getLocalTime(result[i].mtime) + '</td></tr>';
            }
            var mbody = '<div class="divtable" style="height: 395px;overflow: auto;border: #ddd 1px solid;position: relative;"><table class="table table-hover" width="100%" border="0" cellpadding="0" cellspacing="0"><thead><th>' + lan.files.file_name + '</th><th>' + lan.files.file_size + '</th><th>' + lan.files.last_edit_time + '</th></thead>\
						<tbody>' + tbody + '</tbody>\
						</table></div>';
            SafeMessage(lan.files.will_cover_this_file, mbody, function () {
                BatchPasteTo(data, path);
            });
            $(".layui-layer-page").css("width", "500px");
        } else {
            BatchPasteTo(data, path);
        }
    });
}

function BatchPasteTo(data, path) {
    myloadT = layer.msg("<div class='myspeed'>" + lan.public.the + "</div>", {
        icon: 16,
        time: 0,
        shade: [0.3, '#000']
    });
    setTimeout(function () {
        getSpeed('.myspeed');
    }, 1000);
    $.post('files?action=BatchPaste', data, function (rdata) {
        layer.close(myloadT);
        setCookie('BatchSelected', null);
        GetFiles(path);
        layer.msg(rdata.msg, {
            icon: 1
        });
    });
}

function GetExtName(fileName) {
    var extArr = fileName.split(".");
    var exts = ['folder', 'folder-unempty', 'sql', 'c', 'cpp', 'cs', 'flv', 'css', 'js', 'htm', 'html', 'java', 'log', 'mht', 'php', 'url', 'xml', 'ai', 'bmp', 'cdr', 'gif', 'ico', 'jpeg', 'jpg', 'JPG', 'png', 'psd', 'webp', 'ape', 'avi', 'flv', 'mkv', 'mov', 'mp3', 'mp4', 'mpeg', 'mpg', 'rm', 'rmvb', 'swf', 'wav', 'webm', 'wma', 'wmv', 'rtf', 'docx', 'fdf', 'potm', 'pptx', 'txt', 'xlsb', 'xlsx', '7z', 'cab', 'iso', 'bz2', 'rar', 'zip', 'gz', 'bt', 'file', 'apk', 'bookfolder', 'folder', 'folder-empty', 'folder-unempty', 'fromchromefolder', 'documentfolder', 'fromphonefolder', 'mix', 'musicfolder', 'picturefolder', 'videofolder', 'sefolder', 'access', 'mdb', 'accdb', 'sql', 'c', 'cpp', 'cs', 'js', 'fla', 'flv', 'htm', 'html', 'java', 'log', 'mht', 'php', 'url', 'xml', 'ai', 'bmp', 'cdr', 'gif', 'ico', 'jpeg', 'jpg', 'JPG', 'png', 'psd', 'webp', 'ape', 'avi', 'flv', 'mkv', 'mov', 'mp3', 'mp4', 'mpeg', 'mpg', 'rm', 'rmvb', 'swf', 'wav', 'webm', 'wma', 'wmv', 'doc', 'docm', 'dotx', 'dotm', 'dot', 'rtf', 'docx', 'pdf', 'fdf', 'ppt', 'pptm', 'pot', 'potm', 'pptx', 'txt', 'xls', 'csv', 'xlsm', 'xlsb', 'xlsx', '7z', 'gz', 'cab', 'iso', 'rar', 'zip', 'bt', 'file', 'apk', 'css'];
    var extLastName = extArr[extArr.length - 1];
    for (var i = 0; i < exts.length; i++) {
        if (exts[i] == extLastName) {
            return exts[i];
        }
    }
    return 'file';
}

function ShowEditMenu() {
    $("#filesBody > tr").hover(function () {
        $(this).addClass("hover");
    }, function () {
        $(this).removeClass("hover");
    }).click(function () {
        $(this).addClass("on").siblings().removeClass("on");
    })
}

function GetFileName(fileNameFull) {
    var pName = fileNameFull.split('/');
    return pName[pName.length - 1];
}

function GetDisk() {
    var LBody = '';
    $.get('/system?action=GetDiskInfo', function (rdata) {
        for (var i = 0; i < rdata.length; i++) {
            LBody += "<span onclick=\"GetFiles('" + rdata[i].path + "')\"><span class='glyphicon glyphicon-hdd'></span>&nbsp;" + (rdata[i].path == '/' ? lan.files.path_root : rdata[i].path) + "(" + rdata[i].size[2] + ")</span>";
        }
        var trash = '<span id="recycle_bin" onclick="Recycle_bin(\'open\')" title="' + lan.files.recycle_bin_title + '" style="position: absolute; border-color: #ccc; right: 77px;"><span class="glyphicon glyphicon-trash"></span>&nbsp;' + lan.files.recycle_bin_title + '</span>';
        var backups = '<button class="btn btn-default btn-sm pull-left" style="position: absolute; right: 225px;" onclick="manage()">Backup Permissions</button>';
        $("#comlist").html(LBody + trash + backups);
        IsDiskWidth();
    });
}

function BackDir() {
    var str = $("#DirPathPlace input").val().replace('//', '/');
    if (str.substr(str.length - 1, 1) == '/') {
        str = str.substr(0, str.length - 1);
    }
    var Path = str.split("/");
    var back = '/';
    if (Path.length > 2) {
        var count = Path.length - 1;
        for (var i = 0; i < count; i++) {
            back += Path[i] + '/';
        }
        if (back.substr(back.length - 1, 1) == '/') {
            back = back.substr(0, back.length - 1);
        }
        GetFiles(back);
    } else {
        back += Path[0];
        GetFiles(back);
    }
    setTimeout('PathPlaceBtn(getCookie("Path"));', 200);
}

function CreateFile(type, path) {
    if (type == 1) {
        var fileName = $("#newFileName").val();
        layer.msg(lan.public.the, {
            icon: 16,
            time: 10000
        });
        $.post('/files?action=CreateFile', 'path=' + encodeURIComponent(path + '/' + fileName), function (rdata) {
            layer.close(getCookie('layers'));
            layer.msg(rdata.msg, {
                icon: rdata.status ? 1 : 2
            });
            if (rdata.status) {
                GetFiles($("#DirPathPlace input").val());
                openEditorView(0, path + '/' + fileName);
            }
        });
        return;
    }
    var layers = layer.open({
        type: 1,
        shift: 5,
        closeBtn: 2,
        area: '320px',
        title: lan.files.new_empty_file,
        content: '<div class="bt-form pd20 pb70">\
					<div class="line">\
					<input type="text" class="bt-input-text" name="Name" id="newFileName" value="" placeholder="' + lan.files.file_name + '" style="width:100%" />\
					</div>\
					<div class="bt-form-submit-btn">\
					<button type="button" class="btn btn-danger btn-sm layer_close">' + lan.public.close + '</button>\
					<button id="CreateFileBtn" type="button" class="btn btn-success btn-sm" onclick="CreateFile(1,\'' + path + '\')">' + lan.files.new + '</button>\
					</div>\
				</div>',
        success: function (layers, index) {
            $('.layer_close').click(function () {
                layer.close(index);
            });
        }
    });
    setCookie('layers', layers);
    $("#newFileName").focus().keyup(function (e) {
        if (e.keyCode == 13) $("#CreateFileBtn").click();
    });
}

function CreateDir(type, path) {
    if (type == 1) {
        var dirName = $("#newDirName").val();
        layer.msg(lan.public.the, {
            icon: 16,
            time: 10000
        });
        $.post('/files?action=CreateDir', 'path=' + encodeURIComponent(path + '/' + dirName), function (rdata) {
            layer.close(getCookie('layers'));
            layer.msg(rdata.msg, {
                icon: rdata.status ? 1 : 2
            });
            GetFiles($("#DirPathPlace input").val());
        });
        return;
    }
    var layers = layer.open({
        type: 1,
        shift: 5,
        closeBtn: 2,
        area: '320px',
        title: lan.files.new_dir,
        content: '<div class="bt-form pd20 pb70">\
					<div class="line">\
					<input type="text" class="bt-input-text" name="Name" id="newDirName" value="" placeholder="' + lan.files.dir_name + '" style="width:100%" />\
					</div>\
					<div class="bt-form-submit-btn">\
					<button type="button" class="btn btn-danger btn-sm btn-title layer_close">' + lan.public.close + '</button>\
					<button type="button" id="CreateDirBtn" class="btn btn-success btn-sm btn-title" onclick="CreateDir(1,\'' + path + '\')">' + lan.files.new + '</button>\
					</div>\
				</div>',
        success: function (layers, index) {
            $('.layer_close').click(function () {
                layer.close(index);
            });
        }
    });
    setCookie('layers', layers);
    $("#newDirName").focus().keyup(function (e) {
        if (e.keyCode == 13) $("#CreateDirBtn").click();
    });
}
// 删除文件
function DeleteFile(fileName) {
    layer.confirm(lan.get('recycle_bin_confirm', [fileName]), {
        title: lan.files.del_file,
        closeBtn: 2,
        icon: 3
    }, function (index) {
        layer.msg(lan.public.the, {
            icon: 16,
            time: 0,
            shade: [0.3, '#000']
        });
        $.post('/files?action=DeleteFile', 'path=' + encodeURIComponent(fileName), function (rdata) {
            layer.close(index);
            layer.msg(rdata.msg, {
                icon: rdata.status ? 1 : 2
            });
            GetFiles($("#DirPathPlace input").val());
        });
    });
}

function DeleteDir(dirName) {
    layer.confirm(lan.get('recycle_bin_confirm_dir', [dirName]), {
        title: lan.files.del_dir,
        closeBtn: 2,
        icon: 3
    }, function (index) {
        layer.msg(lan.public.the, {
            icon: 16,
            time: 0,
            shade: [0.3, '#000']
        });
        $.post('/files?action=DeleteDir', 'path=' + encodeURIComponent(dirName), function (rdata) {
            layer.close(index);
            layer.msg(rdata.msg, {
                icon: rdata.status ? 1 : 2
            });
            GetFiles($("#DirPathPlace input").val());
        });
    });
}

function AllDeleteFileSub(data, path) {
    layer.confirm(lan.files.del_all_msg, {
        title: lan.files.del_all_file,
        closeBtn: 2,
        icon: 3
    }, function (index) {
        layer.msg("<div class='myspeed'>" + lan.public.the + "</div>", {
            icon: 16,
            time: 0,
            shade: [0.3, '#000']
        });
        setTimeout(function () {
            getSpeed('.myspeed');
        }, 1000);
        $.post('files?action=SetBatchData', data, function (rdata) {
            layer.close(index);
            GetFiles(path);
            layer.msg(rdata.msg, {
                icon: 1
            });
        });
    });
}

function ReloadFiles() {
    setInterval(function () {
        var path = $("#DirPathPlace input").val();
        GetFiles(path);
    }, 3000);
}

function DownloadFile(action) {
    if (action == 1) {
        var fUrl = $("#mUrl").val();
        fUrl = encodeURIComponent(fUrl);
        fpath = $("#dpath").val();
        fname = encodeURIComponent($("#dfilename").val());
        if (!fname) {
            durl = $("#mUrl").val()
            tmp = durl.split('/')
            $("#dfilename").val(tmp[tmp.length - 1])
            fname = encodeURIComponent($("#dfilename").val());
            if (!fname) {
                layer.msg(lan.files.file_name_cant_empty);
                return;
            }
        }
        layer.close(getCookie('layers'))
        layer.msg(lan.files.down_task, {
            time: 0,
            icon: 16,
            shade: [0.3, '#000']
        });
        $.post('/files?action=DownloadFile', 'path=' + fpath + '&url=' + fUrl + '&filename=' + fname, function (rdata) {
            layer.msg(rdata.msg, {
                icon: rdata.status ? 1 : 2
            });
            GetFiles(fpath);
            GetTaskCount();
            task_stat();
        });
        return;
    }
    var path = $("#DirPathPlace input").val();
    var layers = layer.open({
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
					<button type="button" class="btn btn-danger btn-sm layer_close">' + lan.public.close + '</button>\
					<button type="button" id="dlok" class="btn btn-success btn-sm dlok" onclick="DownloadFile(1)">' + lan.public.ok + '</button>\
					</div>\
				</form>',
        success: function (layers, index) {
            $('.layer_close').click(function () {
                layer.close(index)
            });
        }
    });
    setCookie('layers', layers);
    //fly("dlok");
    $("#mUrl").change(function () {
        durl = $(this).val()
        tmp = durl.split('/')
        $("#dfilename").val(tmp[tmp.length - 1])
    });
}

function ExecShell(action) {
    if (action == 1) {
        var path = $("#DirPathPlace input").val();
        var exec = encodeURIComponent($("#mExec").val());
        $.post('/files?action=ExecShell', 'path=' + path + '&shell=' + exec, function (rdata) {
            if (rdata.status) {
                $("#mExec").val('');
                GetShellEcho();
            } else {
                layer.msg(rdata.msg, {
                    icon: rdata.status ? 1 : 2
                });
            }

        });
        return;
    }
    layer.open({
        type: 1,
        shift: 5,
        closeBtn: 2,
        area: ['70%', '600px'],
        title: lan.files.shell_title,
        content: '<div class="bt-form pd15">\
					<div class="shellcode"><pre id="Result"></pre></div>\
					<div class="line">\
					<input type="text" class="bt-input-text" name="exec" id="mExec" value="" placeholder="' + lan.files.shell_ps + '" onkeydown="if(event.keyCode==13)ExecShell(1);" /><span class="shellbutton btn btn-default btn-sm pull-right" onclick="ExecShell(1)" style="width:10%">' + lan.files.shell_go + '</span>\
					</div>\
				</div>'
    });
    setTimeout(function () {
        outTimeGet();
    }, 1000);

}

var outTime = null;

function outTimeGet() {
    outTime = setInterval(function () {
        if (!$("#mExec").attr('name')) {
            clearInterval(outTime);
            return;
        }
        GetShellEcho();
    }, 1000);
}

function GetShellEcho() {
    $.post('/files?action=GetExecShellMsg', '', function (rdata) {
        $("#Result").html(rdata);
        $(".shellcode").scrollTop($(".shellcode")[0].scrollHeight);
    });
}

function ReName(type, fileName) {
    if (type == 1) {
        var path = $("#DirPathPlace input").val();
        var newFileName = encodeURIComponent(path + '/' + $("#newFileName").val());
        var oldFileName = encodeURIComponent(path + '/' + fileName);
        layer.msg(lan.public.the, {
            icon: 16,
            time: 10000
        });
        $.post('/files?action=MvFile', 'sfile=' + oldFileName + '&dfile=' + newFileName + '&rename=true', function (rdata) {
            layer.close(getCookie('layers'));
            layer.msg(rdata.msg, {
                icon: rdata.status ? 1 : 2
            });
            GetFiles(path);
        });
        return;
    }
    var layers = layer.open({
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
				<button type="button" class="btn btn-danger btn-sm btn-title layers_close">' + lan.public.close + '</button>\
				<button type="button" id="ReNameBtn" class="btn btn-success btn-sm btn-title" onclick="ReName(1,\'' + fileName.replace(/'/, "\\'") + '\')">' + lan.public.save + '</button>\
				</div>\
			</div>',
        success: function (layers, index) {
            $('.layers_close').click(function () {
                layer.close(index);
            });
        }
    });
    setCookie('layers', layers);
    $("#newFileName").focus().keyup(function (e) {
        if (e.keyCode == 13) $("#ReNameBtn").click();
    });
}

function CutFile(fileName) {
    var path = $("#DirPathPlace input").val();
    setCookie('cutFileName', fileName);
    setCookie('copyFileName', null);
    layer.msg(lan.files.mv_ok, {
        icon: 1,
        time: 1000
    });
    GetFiles(path);
}

function CopyFile(fileName) {
    var path = $("#DirPathPlace input").val();
    setCookie('copyFileName', fileName);
    setCookie('cutFileName', null);
    layer.msg(lan.files.copy_ok, {
        icon: 1,
        time: 1000
    });
    GetFiles(path);
}

function PasteFile(fileName) {
    var path = $("#DirPathPlace input").val();
    var copyName = getCookie('copyFileName');
    var cutName = getCookie('cutFileName');
    var filename = copyName;
    if (cutName != 'null' && cutName != undefined) filename = cutName;
    filename = filename.split('/').pop();
    $.post('/files?action=CheckExistsFiles', {
        dfile: path,
        filename: filename
    }, function (result) {
        if (result.length > 0) {
            var tbody = '';
            for (var i = 0; i < result.length; i++) {
                tbody += '<tr><td>' + result[i].filename + '</td><td>' + ToSize(result[i].size) + '</td><td>' + getLocalTime(result[i].mtime) + '</td></tr>';
            }
            var mbody = '<div class="divtable"><table class="table table-hover" width="100%" border="0" cellpadding="0" cellspacing="0"><thead><th>' + lan.files.file_name + '</th><th>' + lan.files.file_size + '</th><th>' + lan.files.last_edit_time + '</th></thead>\
						<tbody>' + tbody + '</tbody>\
						</table></div>';
            SafeMessage(lan.files.will_cover_this_file, mbody, function () {
                PasteTo(path, copyName, cutName, fileName);
            });
        } else {
            PasteTo(path, copyName, cutName, fileName);
        }
    });
}


function PasteTo(path, copyName, cutName, fileName) {
    if (copyName != 'null' && copyName != undefined) {
        layer.msg(lan.files.copy_the, {
            icon: 16,
            time: 0,
            shade: [0.3, '#000']
        });
        $.post('/files?action=CopyFile', 'sfile=' + encodeURIComponent(copyName) + '&dfile=' + encodeURIComponent(path + '/' + fileName), function (rdata) {
            layer.closeAll();
            layer.msg(rdata.msg, {
                icon: rdata.status ? 1 : 2
            });
            GetFiles(path);
        });
        setCookie('copyFileName', null);
        setCookie('cutFileName', null);
        return;
    }

    if (cutName != 'null' && cutName != undefined) {
        layer.msg(lan.files.mv_the, {
            icon: 16,
            time: 0,
            shade: [0.3, '#000']
        });
        $.post('/files?action=MvFile', 'sfile=' + encodeURIComponent(cutName) + '&dfile=' + encodeURIComponent(path + '/' + fileName), function (rdata) {
            layer.closeAll();
            layer.msg(rdata.msg, {
                icon: rdata.status ? 1 : 2
            });
            GetFiles(path);
        });
        setCookie('copyFileName', null);
        setCookie('cutFileName', null);
    }
}
// 压缩文件
function Zip(dirName, submits) {
    var path = $("#DirPathPlace input").val();
    if (submits != undefined) {
        if (dirName.indexOf(',') == -1) {
            tmp = $("#sfile").val().split('/');
            sfile = encodeURIComponent(tmp[tmp.length - 1]);
        } else {
            sfile = encodeURIComponent(dirName);
        }
        dfile = encodeURIComponent($("#dfile").val());
        var z_type = $("select[name='z_type']").val();
        if (!z_type) z_type = 'tar.gz';
        layer.close(getCookie('layers'));
        var layers = layer.msg(lan.files.zip_the, {
            icon: 16,
            time: 0,
            shade: [0.3, '#000']
        });
        $.post('/files?action=Zip', 'sfile=' + sfile + '&dfile=' + dfile + '&z_type=' + z_type + '&path=' + encodeURIComponent(path), function (rdata) {
            layer.close(layers);
            if (rdata == null || rdata == undefined) {
                layer.msg(lan.files.zip_ok, {
                    icon: 1
                });
                GetFiles(path)
                ReloadFiles();
                return;
            }
            layer.msg(rdata.msg, {
                icon: rdata.status ? 1 : 2
            });
            if (rdata.status) {
                task_stat()
                GetFiles(path);
            }
        });
        return
    }

    param = dirName;
    if (dirName.indexOf(',') != -1) {
        tmp = path.split('/')
        dirName = path + '/' + tmp[tmp.length - 1]
    }

    var layers = layer.open({
        type: 1,
        shift: 5,
        closeBtn: 2,
        area: '650px',
        title: lan.files.zip_title,
        content: '<div class="bt-form pd20 pb70">' +
            '<div class="line noborder">' +
            '<input type="text" class="form-control" id="sfile" value="' + param + '" placeholder="" style="display:none" />' +
            '<p style="margin-bottom: 10px;"><span>' + lan.files.comp_type + '</span><select style="margin-left: 8px;" class="bt-input-text" name="z_type"><option value="tar.gz">tar.gz (' + lan.files.recommend + ')</option><option value="zip">zip (' + lan.files.general_format + ')</option><option value="rar">rar (' + lan.files.compatibility_better_chinese + ')</option></select></p>' +
            '<span>' + lan.files.zip_to + '</span><input type="text" class="bt-input-text" id="dfile" value="' + dirName + '.tar.gz" placeholder="' + lan.files.zip_to + '" style="width: 75%; display: inline-block; margin: 0px 10px 0px 20px;" /><span class="glyphicon glyphicon-folder-open cursor" onclick="ChangePath(\'dfile\')"></span>' +
            '</div>' +
            '<div class="bt-form-submit-btn">' +
            '<button type="button" class="btn btn-danger btn-sm btn-title layer_close">' + lan.public.close + '</button>' +
            '<button type="button" id="ReNameBtn" class="btn btn-success btn-sm btn-title" onclick="Zip(\'' + param + '\',1)">' + lan.files.file_menu_zip + '</button>' +
            '</div>' +
            '</div>',
        success: function (layers, index) {
            $('.layer_close').click(function () {
                layer.close(index);
            });
        }
    });
    setCookie('layers', layers);
    setTimeout(function () {
        $("select[name='z_type']").change(function () {
            var z_type = $(this).val();
            dirName = dirName.replace("tar.gz", z_type)
            $("#dfile").val(dirName + '.' + z_type);
        });
    }, 100);

}

function UnZip(fileName, type) {
    var path = $("#DirPathPlace input").val();
    if (type.length == 3) {
        var sfile = encodeURIComponent($("#sfile").val());
        var dfile = encodeURIComponent($("#dfile").val());
        var password = encodeURIComponent($("#unpass").val());
        coding = $("select[name='coding']").val();
        layer.close(getCookie('layers'));
        layer.msg(lan.files.unzip_the, {
            icon: 16,
            time: 0,
            shade: [0.3, '#000']
        });
        $.post('/files?action=UnZip', 'sfile=' + sfile + '&dfile=' + dfile + '&type=' + type + '&coding=' + coding + '&password=' + password, function (rdata) {
            layer.msg(rdata.msg, {
                icon: rdata.status ? 1 : 2
            });
            task_stat();
            GetFiles(path);
        });
        return
    }

    type = (type == 1) ? 'tar' : 'zip'
    var umpass = '';
    if (type == 'zip') {
        umpass = '<div class="line"><span class="tname">' + lan.files.zip_pass_title + '</span><input type="text" class="bt-input-text" id="unpass" value="" placeholder="' + lan.files.zip_pass_msg + '" style="width:330px" /></div>'
    }
    var layers = layer.open({
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
            '<button type="button" class="btn btn-danger btn-sm btn-title layer_close">' + lan.public.close + '</button>' +
            '<button type="button" id="ReNameBtn" class="btn btn-success btn-sm btn-title" onclick="UnZip(\'' + fileName + '\',\'' + type + '\')">' + lan.files.file_menu_unzip + '</button>' +
            '</div>' +
            '</div>',
        success: function (layers, index) {
            $('.layer_close').click(function () {
                layer.close(index);
            });
        }
    });
    setCookie('layers', layers);
}

function isZip(fileName) {
    var ext = fileName.split('.');
    var extName = ext[ext.length - 1].toLowerCase();
    if (extName == 'zip' || extName == 'war' || extName == 'rar') return 0;
    if (extName == 'gz' || extName == 'tgz' || extName == 'bz2') return 1;
    return -1;
}

function isText(fileName) {
    var exts = ['rar', 'war', 'zip', 'tar.gz', 'gz', 'iso', 'xsl', 'doc', 'xdoc', 'jpeg', 'jpg', 'png', 'gif', 'bmp', 'tiff', 'exe', 'so', '7z', 'bz', 'bz2'];
    return isExts(fileName, exts) ? false : true;
}

function isImage(fileName) {
    var exts = ['jpg', 'jpeg', 'png', 'bmp', 'gif', 'tiff', 'ico'];
    return isExts(fileName, exts);
}

function isVideo(fileName) {
    var exts = ['mp4', 'mpeg', 'mpg', 'mov', 'avi', 'webm', 'mkv'];
    return isExts(fileName, exts);
}

function isPhp(fileName) {
    var exts = ['php'];
    return isExts(fileName, exts);
}

function isExts(fileName, exts) {
    var ext = fileName.split('.');
    if (ext.length < 2) return false;
    var extName = ext[ext.length - 1].toLowerCase();
    for (var i = 0; i < exts.length; i++) {
        if (extName == exts[i]) return true;
    }
    return false;
}

function GetImage(fileName) {
    var imgUrl = '/download?filename=' + fileName;
    layer.open({
        type: 1,
        closeBtn: 2,
        title: false,
        area: '500px',
        shadeClose: true,
        content: '<div class="showpicdiv"><img width="100%" src="' + imgUrl + '"></div>'
    });
    $(".layui-layer").css("top", "30%");
}

// function GetPlay(fileName) {
//     var imgUrl = '/download?filename=' + fileName;
//     layer.open({
//         type: 1,
//         closeBtn: 2,
//         title: 'Play [' + fileName + ']',
//         area: '500px',
//         shadeClose: false,
//         content: '<div class="showpicdiv"><video src="' + imgUrl + '" controls="controls" autoplay="autoplay" width="100%" type="video/mp4">\
//                     Your browser does not support the video tag.\
//                     </video></div>'
//     });
//     $(".layui-layer").css("top", "30%");
// }
function play_file(obj,filename) {
    console.log($('#btvideo video').attr('data-filename'),filename)
    if($('#btvideo video').attr('data-filename')== filename) return false;
    var imgUrl = '/download?filename=' + filename + '&play=true';
    var v = '<video src="' + imgUrl +'" controls="controls" data-fileName="'+ filename +'" autoplay="autoplay" width="640" height="360">\
        Your browser does not support Video Tags.\
                    </video>'
    $("#btvideo").html(v);
    var p_tmp = filename.split('/')
    $(".btvideo-title").html(p_tmp[p_tmp.length-1]);
    $(".video-avt").removeClass('video-avt');
    $(obj).parents('tr').addClass('video-avt');
}
function GetPlay(fileName) {
    var old_filename = fileName;
    var imgUrl = '/download?filename=' + fileName;
    var p_tmp = fileName.split('/')
    var path = p_tmp.slice(0, p_tmp.length - 1).join('/')
    layer.open({
        type: 1,
        closeBtn: 2,
        // maxmin:true,
        title: 'Playing [<a class="btvideo-title">' + p_tmp[p_tmp.length-1] + '</a>]',
        area: ["890px","402px"],
        shadeClose: false,
        skin:'movie_pay',
        content: '<div id="btvideo"><video type="" src="' + imgUrl + '&play=true" data-filename="'+ fileName +'" controls="controls" autoplay="autoplay" width="640" height="360">\
            Your browser does not support Video Tags.\
                    </video></div><div class="video-list"></div>',
        success: function () {
            $.post('/files?action=get_videos', { path: path }, function (rdata) {
                var video_list = '<table class="table table-hover" style=""><thead style="display: none;"><tr><th style="word-break: break-all;word-wrap:break-word;width:165px;">File name</th><th style="width:65px" style="text-align:right;">Size</th></tr></thead>';
                for (var i = 0; i < rdata.length; i++) {
                    var filename = path + '/' + rdata[i].name
                    video_list += '<tr class="' + ((filename === old_filename) ? 'video-avt' :'') + '"><td style="word-break: break-all;word-wrap:break-word;width:150px" onclick="play_file(this,\'' + filename + '\')" title="File: ' + filename + '\ntype: ' + rdata[i].type + '"><a>'
                        + rdata[i].name + '</a></td><td style="font-size: 8px;text-align:right;width:65px;">' + ToSize(rdata[i].size) + '</td></tr>';
                }
                video_list += '</table>';
                $('.video-list').html(video_list);
            });
        }
    });
}
function GetFileBytes(fileName, fileSize) {
    window.open('/download?filename=' + encodeURIComponent(fileName));
}

function UploadFiles() {

    var path = $("#DirPathPlace input").val() + "/";
    bt_upload_file.open(path, null, null, function (path) {
        GetFiles(path);
    });
    return;

    /*
	layer.open({
		type:1,
		closeBtn: 2,
		title:lan.files.up_title,
		area: ['500px','500px'],
		shadeClose:false,
		content:'<div class="fileUploadDiv"><input type="hidden" id="input-val" value="'+path+'" />\
				<input type="file" id="file_input"  multiple="true" autocomplete="off" />\
				<button type="button"  id="opt" autocomplete="off">'+lan.files.up_add+'</button>\
				<button type="button" id="up" autocomplete="off" >'+lan.files.up_start+'</button>\
				<span id="totalProgress" style="position: absolute;top: 7px;right: 147px;"></span>\
				<span style="float:right;margin-top: 9px;">\
				<font>'+lan.files.up_coding+':</font>\
				<select id="fileCodeing" >\
					<option value="byte">'+lan.files.up_bin+'</option>\
					<option value="utf-8">UTF-8</option>\
					<option value="gb18030">GB2312</option>\
				</select>\
				</span>\
				<button type="button" id="filesClose" autocomplete="off" onClick="layer.closeAll()" >'+lan.public.close+'</button>\
				<ul id="up_box"></ul></div>'
	});
	UploadStart();*/
}

// 设置权限
function Oksend(data, loadT) {
    $.post('files?action=SetFileAccess', data, function (rdata) {
        layer.close(loadT);
        if (rdata.status) layer.close(getCookie('layers'));
        layer.msg(rdata.msg, {
            icon: rdata.status ? 1 : 2
        });
        var path = $("#DirPathPlace input").val();
        GetFiles(path)
    });
}
//还原备份
function restore(restore_time) {
    var sub_type = $("#accept_all").prop("checked") ? 1 : 0,
    file = $(".layui-layer-title").text();
    file = file.match(/\[(.+?)\]/g);
    file = file[0].substring(1, file[0].length - 1);
    var layerss = layer.open({
        type: 1,
        closeBtn: 2,
        title: 'Confirm restore?',
        area: '330px',
        shadeClose: false,
        btn: ['Yes', 'No'],
        content: '<div style="padding: 20px;font-size: 14px;">\
                    Restore would overwrite the current settings, continue?\
                </div>',
        yes: function (layerss, index) {
            $.post('/files?action=restore_path_permissions', {
                restore_sub_dir: sub_type,
                date: restore_time,
                path: file
            }, function (edata) {
                layer.closeAll();
                layer.msg(edata.msg, {
                    icon: 1,
                    time: 1900
                });
            });
        },
        btn2: function () {
            layer.close(layerss);
        },
        cancel: function () {
            layer.close(layerss);
        }
    });
}
//删除备份
function delback(id) {
	layer.confirm('The backup cannot be restored after deletion.<br>Continue to delete?',{title: 'Confirm delete？',btn: ['Yes', 'No'],closeBtn:2},function(index, layero){
    	$.post('/files?action=del_path_premissions', {
            id: id
        }, function (edata) {
            var file = $(".layui-layer-title:eq(0)").text();
            if(file!=='Manage Backups'){
	    		file = file.match(/\[(.+?)\]/g);
	    		file = file[0].substring(1, file[0].length - 1);
	            backup_file(file);
            }else{
            	$(".allback tbody tr[data-id=" + id + "]").remove();
            }
            layer.msg(edata.msg, { icon: edata.status ? 1 : 2 });
        });
    });
    // var layerss = layer.open({
    //     type: 1,
    //     closeBtn: 2,
    //     title: 'Confirm delete',
    //     area: '330px',
    //     shadeClose: false,
    //     btn: ['yes', 'no'],
    //     content: '<div style="padding: 20px;">The backup cannot be restored after deletion.<br>Continue to delete?</div>',
    //     yes: function (layerss) {
    //         layer.close(layerss);
    //         $.post('/files?action=del_path_premissions', {
    //             id: id
    //         }, function (edata) {
    //             $(".allback tbody tr[data-id=" + id + "]").remove();
    //             $(".sel ul li[data-id=" + id + "]").remove();
    //         });
    //     },
    //     btn2: function () {
    //         layer.close(layerss);
    //     },
    //     cancel: function () {
    //         layer.close(layerss);
    //     }
    // });
}
//全部文件备份列表
function backup_list() {
    var all_back = '';
    $.ajaxSettings.async = false;
    $.post('/files?action=get_all_back', function (edata) {
        //for (let i in edata) {
        for (var i = 0; i < edata.length; i++) {
            var d = new Date(edata[i][2] * 1000);
            var minut = d.getMinutes();
            var hours = d.getHours();
            var second = d.getSeconds();
            if (minut <= 9) minut = '0' + minut + '';
            if (hours <= 9) hours = '0' + hours + '';
            if (second <= 9) second = '0' + second + '';
            var date = (d.getFullYear()) + "/" +
                (d.getMonth() + 1) + "/" +
                (d.getDate()) + " " +
                (hours) + ":" + (minut) + ":" + (second);
            all_back += '<tr style="padding: 5px;margin: 0;border: #e6e6e6 1px solid;border-top: none;" data-id="' + edata[i][0] + '">\
                <td>' + date + '</td>\
                <td style="max-width: 297px;min-width: 297px;">\
                    <a style="width: 287px;overflow: hidden;text-overflow: ellipsis;white-space: nowrap;display: inline-block;" class="btlink"  title="' + edata[i][3] + '" href="javascript:openPath(\'' + edata[i][3] + '\');">' + edata[i][3] + '</a>\
                </td>\
                <td style="max-width: 77px;min-width: 77px;overflow: hidden;text-overflow: ellipsis;text-align: left;" title="' + edata[i][1] + '">' + edata[i][1] + '</td>\
                <td style="min-width: 60px;text-align: center;"><a onclick="delback(' + edata[i][0] + ')" class="btlink">Del</a></td>\
            </tr>';
        }
    });
    $.ajaxSettings.async = true;
    return all_back;
}
//管理备份
function manage() {
    var all_back = backup_list();
    var layerss = layer.open({
        type: 1,
        closeBtn: 2,
        title: 'Manage Backups',
        area: ['630px', '500px'],
        shadeClose: false,
        content: '<div class="allback pd20" style="padding-bottom: 0;">\
                    <div class="info-r c4 mb15 text-left relative">\
                        <input class="bt-input-text" id="server_path" type="text" name="path" placeholder="Please select the project path" style="width:75%;">\
                        <div style="display: inline-block;position: absolute;right:0;text-align: right;">\
                            <span data-id="path" class="glyphicon cursor glyphicon-folder-open" style="margin-right: 31px;" onclick="change_path(\'#server_path\',\'dir\')"></span>\
                            <button class="btn btn-success btn-sm btn-backup" onclick="backup(\'\',0)">Backup</button>\
                        </div>\
                    </div>\
                    <table class="text-left table table-hover" style="margin-bottom: 0;">\
		            	<thead style="background: #f6f6f6;margin: 0;border: #e6e6e6 1px solid;border-bottom: none;">\
		            		<tr>\
		            			<th style="color: #666;font-weight: 600;padding: 10px 8px;width: 151px;border-bottom: none;">Backup time</th>\
		            			<th style="color: #666;font-weight: 600;padding: 10px 8px;width: 290px;border-bottom: none;">Backup path</th>\
		            			<th style="color: #666;font-weight: 600;padding: 10px 8px;text-align: center;border-bottom: none;">Name</th>\
		            			<th style="color: #666;font-weight: 600;padding: 10px 8px;text-align: center;border-bottom: none;">Delect</th>\
		            		</tr>\
		            	</thead>\
                    </table>\
                    <div style="height: 337px;overflow: auto;">\
                        <table class="text-left table table-hover">\
		                	<tbody class="buplist">\
                                ' + all_back + '\
		                	</tbody>\
                        </table>\
                    </div>\
                </div>',
        cancel: function () {
            layer.close(layerss);
        }
    });
}
//备份
function backup(file, type) {
    //文件夹type为0
    var sub_type = 1;
    if (type == 1) {
        sub_type = $("#accept_all").prop("checked") ? 1 : 0;
        file = file.split(1, file.length - 1)[0];
    } else if (type == 0) {
        file = $("#server_path").val();
    }
    if (file == '' || typeof (file) == 'undefined') {
        layer.msg('Please select a directory or file', {
            icon: 2,
            time: 1900
        });
        return false;
    }
    var layerss = layer.open({
        type: 1,
        closeBtn: 2,
        title: 'Confirm backup?',
        area: '300px',
        shadeClose: false,
        btn: ['Yes', 'No'],
        content: '<div style="padding: 20px;margin: 0;font-size: 13px;">\
                        <p style="padding: 8px 5px;font-size: 13px;">Please enter the current backup name</p>\
                        <div>Remarks\
                            <input type="text" class="form-control ml5 mt10" placeholder="Please enter name" style="width: 179px;display: inline-block;">\
                        </div>\
                    </div>',
        yes: function (layerss, index) {
            $('.layer_close').click(function () {
                layer.close(index);
            });
            $.post('/files?action=back_path_permissions', {
                back_sub_dir: sub_type,
                path: file,
                remark: $("input.form-control").val()
            }, function (edata) {
                if (!edata.status) {
                    layer.msg(edata.msg, {
                        time: 1900,
                        icon: 2,
                    });
                    layer.close(layerss);
                    return false;
                }
                layer.close(layerss);
                layer.msg(edata.msg, {
                    time: 1900,
                    icon: 1,
                });
                if (type == 0) {
                    var new_back = backup_list();
                    $(".buplist").html(new_back);
                } else if (type == 3) {
                    var chmod = $("#access").val();
                    var chown = $("#chown").val();
                    var all = $("#accept_all").prop("checked") ? 'True' : 'False';
                    var data = 'filename=' + encodeURIComponent(file) + '&user=' + chown + '&access=' + chmod + '&all=' + all;
                    Oksend(data);
                    layer.closeAll();
                }
            });
        },
        btn2: function () {
            layer.close(layerss);
        },
        cancel: function () {
            layer.close(layerss);
        }
    });
}
// 选择目录
function change_path(el, type) {
    var _this = this;
    layer.open({
        type: 1,
        area: "750px",
        title: type == 'files' ? 'Select project startup file' : 'Select project directory',
        closeBtn: 2,
        shift: 5,
        shadeClose: false,
        content: "<div class='changepath'>\
                    <div class='path-top'>\
                        <button type='button' class='btn btn-default btn-sm btn-back-file'><span class='glyphicon glyphicon-share-alt'></span>" + lan.public.return+"</button>\
                        <div class='place' id='PathPlace'>" + lan.bt.path + "：<span></span></div>\
                    </div>\
                    <div class='path-con'>\
                        <div class='path-con-left' style='width: 160px;'>\
                            <dl><dt id='changecomlist' onclick='BackMyComputer()'><span class='glyphicon glyphicon-hdd'></span>" + lan.bt.comp + "</dt></dl>\
                        </div>\
                        <div class='path-con-right' style='width: 590px;'>\
                            <ul class='default' id='computerDefautl'></ul>\
                            <div class='divtable'>\
                                <table class='table table-hover' id='table_thead' style='border:0 none'>\
                                    <thead><tr class='file-list-head'><th width='6%'></th><th width='30%'>" + lan.bt.filename + "</th><th width='25%'>" + lan.bt.etime + "</th><th width='10%'>" + lan.bt.access + "</th><th width='10%'>" + lan.bt.own + "</th><th width='10%'></th></tr></thead>\
                                </table>\
                            </div>\
                            <div class='file-list divtable'>\
                                <table class='table table-hover' style='border:0 none;margin-top: -32px;'>\
                                    <thead><tr class='file-list-head'><th width='6%'></th><th width='30%'>" + lan.bt.filename + "</th><th width='25%'>" + lan.bt.etime + "</th><th width='10%'>" + lan.bt.access + "</th><th width='10%'>" + lan.bt.own + "</th><th width='10%'></th></tr></thead>\
                                    <tbody id='dir_tbody' class='list-list'></tbody>\
                                </table>\
                            </div>\
                        </div>\
                    </div>\
                </div>\
                <div class='getfile-btn' style='margin-top:0'>\
                    <button type='button' class='btn btn-default btn-sm pull-left btn_create_folder'>" + lan.bt.adddir + "</button>\
                    <button type='button' class='btn btn-danger btn-sm mr5 btn_close'>" + lan.public.close + "</button>\
                    <button type='button' class='btn btn-success btn-sm btn_path_ok'>" + lan.bt.path_ok + "</button>\
                </div>",
        success: function (layero, index) {
            //设置文件目录
            switch (type) {
                case 'dir':
                    setCookie('file_paths', $(el).val() || '/www');
                    break;
                case 'files':
                    setCookie('file_paths', _this.back_file());
                case 'other':
                    break;
            }
            // 返回目录
            $('.btn-back-file').click(function () {
                setCookie('file_paths', _this.back_file());
                _this.get_dir_dom(type);
            });
            // 关闭layer
            $('.btn_close').click(function () {
                layer.close(index);
            });
            // 选择目录或文件
            $('.btn_path_ok').click(function () {
                var file_name = $('#dir_tbody .ui-selected').find('.open_files_event').attr('data-name');
                var types = $('#dir_tbody .ui-selected').find('.open_files_event').attr('data-type');
                switch (type) {
                    case 'dir':
                        if (file_name == undefined) file_name = '';
                        break;
                    case 'files':
                        if ($('#dir_tbody .ui-selected').length == 0) layer.msg('Please select a file', {
                            icon: 2
                        });
                        return false;
                        break;
                    case 'other':
                        if (file_name == undefined) file_name = '';
                        break;
                }
                var paths = getCookie('file_paths');
                var paths_arry = paths.split('/');
                if (paths_arry[paths_arry.length - 1] != '') {
                    paths += '/'
                }
                $(el).val(paths + (file_name == '' ? '' : file_name));
                layer.close(index)
            });
            // 新建文件夹
            $('.btn_create_folder').click(function () {
                var isCreate = $('#dir_tbody tr:eq(0)').hasClass('table_add_dir');
                if (isCreate) return false;
                $('#dir_tbody').prepend('<tr class="table_add_dir">\
                        <td></td><td colspan="2"><span class="glyphicon glyphicon-folder-open"></span><input class="newFolderName" type="text" value="" style="width: 250px;height: 30px;vertical-align: bottom;">\
                        <td colspan="3"><button type="button" class="btn btn-success btn-sm newFolderEvent">Confirm</button>&nbsp;&nbsp;<button type="button" class="btn btn-default btn-sm newFolderClaer">Cancel</button></td>\
                    </td></tr>');
                document.getElementsByClassName('file-list')[0].scrollTop = 0;
                setTimeout(function () {
                    $('.table_add_dir').on('click', '.newFolderEvent', function (e) {
                        var fileName = $('.newFolderName').val();
                        if (fileName == '') {
                            layer.msg('Please enter a new file name', {
                                icon: 0
                            });
                            return false;
                        }
                        _this.new_folder_event(getCookie('file_paths') + '/' + fileName, function (res) {
                            $(this).parent().parent().remove();
                            _this.get_dir_dom(type);
                        });
                        e.stopPropagation();
                    });
                    $('.table_add_dir').on('click', '.newFolderClaer', function (e) {
                        $(this).parent().parent().remove();
                        e.stopPropagation();
                    });
                }, 500);
            });
            // 磁盘目录跳转
            $('.path-con-left').on('click', '.open_disk', function () {
                var dir = $(this).attr('data-dir');
                setCookie('file_paths', dir)
                _this.get_dir_dom(type);
            });
            // 选择文目录或文件
            $('#dir_tbody').on('click', 'tr', function (e) {
                $(this).find('input[type="checkbox"]').click();
                e.stopPropagation();
            });
            // 选择文件或目录
            $('#dir_tbody').on('click', 'tr input[type="checkbox"]', function (e) {
                var checked = $(this).prop('checked');
                if (!checked) {
                    _this.select = '';
                    $(this).parent().parent().removeClass('ui-selected');
                } else {
                    _this.select = $(this).attr('data-name');
                    $(this).parent().parent().addClass('ui-selected').siblings().removeClass('ui-selected').find('input').prop('checked', false);
                }
                e.stopPropagation();
            });
            // 跳转指定目录，获取选择文件
            $('#dir_tbody').on('click', '.open_files_event', function (e) {
                var type = $(this).attr('data-type');
                var name = $(this).attr('data-name');
                var path = getCookie('file_paths');
                if (type == 'dir') {
                    setCookie('file_paths', path + '/' + name);
                    _this.get_dir_dom(type);
                } else {
                    $(this).parent().prev().find('input[type="checkbox"]').click();
                }
                e.stopPropagation();
            })
            // 跳转指定目录
            $('#dir_tbody').on('click', '.open_files_event .path-con-left dl', function (e) {
                var path = $(this).attr('data-name');
                e.stopPropagation();
            });
            // 跳转指定下一层目录
            $('#dir_tbody').on('dblclick', 'tr', function (e) {
                $(this).find('.open_files_event').click();
                e.stopPropagation();
            });
            //获取目录DOM
            _this.get_dir_dom(type);
        }
    });
}
//获取目录DOM
function get_dir_dom(type) {
    var _this = this;
    this.get_dirk_list(function (res) {
        $('.path-con-right .file-list').show();
        var dir = res.DIR,
            files = res.FILES,
            disk = res.DISK,
            path = res.PATH,
            page = res.PAGE,
            dir_html = '',
            files_html = '',
            disk_html = '';
        for (var i = 0; i < dir.length; i++) {
            var dir_arry = dir[i].split(';');
            dir_html += '<tr class="table_dir"><td class="label_checkbox"><input type="checkbox" name="dir_input" data-name="' + dir_arry[0] + '"/></td><td><a href="javascript:;" data-name="' + dir_arry[0] + '" data-type="dir" class="open_files_event"><span class="glyphicon glyphicon-folder-open"></span><span class="dir_block" style="width:130px;">' + dir_arry[0] + '</span></td><td>' + getLocalTime(dir_arry[2]) + '</td><td>' + dir_arry[3] + '</td><td>' + dir_arry[4] + '</td><td style="text-align: center;"><span class="glyphicon glyphicon-option-horizontal" aria-hidden="true"></span></td></tr>'
        }
        for (var j = 0; j < files.length; j++) {
            var files_arry = files[j].split(';');
            files_html += '<tr class="table_files"><td class="label_checkbox"><input type="checkbox" name="dir_input" data-name="' + files_arry[0] + '"/></td><td><a href="javascript:;"  data-name="' + files_arry[0] + '" data-type="file" class="open_files_event"><span class="ico-default ico-' + _this.obtain_suffix(files_arry[0]) + '"></span><span class="dir_block" style="width:130px;">' + files_arry[0] + '</span></a></td><td>' + getLocalTime(files_arry[2]) + '</td><td>' + files_arry[3] + '</td><td>' + files_arry[4] + '</td><td style="text-align: center;position: relative;"><span class="glyphicon glyphicon-option-horizontal" aria-hidden="true"></span></td></tr>'
        }
        for (var z = 0; z < disk.length; z++) {
            var disk_info = disk[z];
            var dir_list = disk_info.path.split('/');
            dir_list = dir_list[dir_list.length - 1];
            disk_html += '<dt class="open_disk" data-dir="' + disk_info.path + '"><span class="glyphicon glyphicon-hdd"></span>' + (disk_info.path == '/' ? 'Root Dir (' + disk_info.size[2] + ')' : '<span class="table_self_conter" style="width:100px" title="' + disk_info.path + ' (' + disk_info.size[2] + ')">' + dir_list + ' (' + disk_info.size[2] + ')</span>') + '</dt>'
        }
        setCookie('file_paths', path);
        $('.changepath .path-con-left dl').html(disk_html);
        $('#dir_tbody').html(dir_html + files_html);
        $('#PathPlace span').html(path);
    });
}
// 获取文件列表
function get_dirk_list(callback) {
    var dir = getCookie('file_paths');
    dir = dir.replace(/\/\//g, "/");
    this.send({
        url: '/files?action=GetDir',
        tips: 'Getting file list, please wait...',
        data: {
            path: dir,
            disk: 'True'
        },
        success: function (res) {
            if (typeof (res.status) !== "undefined") {
                if (!res.status) {
                    layer.msg(res.msg, {
                        icon: 2
                    });
                    setCookie('file_paths', back_file());
                    return;
                }
            }
            if (callback) callback(res);
        }
    })
}
// 过滤一级目录
function back_file() {
    c = getCookie('file_paths');
    if (c == '/') return '/'
    if (c.substr(c.length - 1, 1) == "/") {
        c = c.substr(0, c.length - 1)
    }
    var d = c.split("/");
    var a = "";
    if (d.length > 1) {
        var e = d.length - 1;
        for (var b = 0; b < e; b++) {
            a += d[b] + "/"
        }
        return a.replace("//", "/")
    } else {
        a = d[0]
    }
    if (d.length == 1) {}
}
// 获取后缀
function obtain_suffix(fileName) {
    var extArr = fileName.split(".");
    var exts = ['folder', 'folder-unempty', 'sql', 'c', 'cpp', 'cs', 'flv', 'css', 'js', 'htm', 'html', 'java', 'log', 'mht', 'php', 'url', 'xml', 'ai', 'bmp', 'cdr', 'gif', 'ico', 'jpeg', 'jpg', 'JPG', 'png', 'psd', 'webp', 'ape', 'avi', 'flv', 'mkv', 'mov', 'mp3', 'mp4', 'mpeg', 'mpg', 'rm', 'rmvb', 'swf', 'wav', 'webm', 'wma', 'wmv', 'rtf', 'docx', 'fdf', 'potm', 'pptx', 'txt', 'xlsb', 'xlsx', '7z', 'cab', 'iso', 'rar', 'zip', 'gz', 'bt', 'file', 'apk', 'bookfolder', 'folder', 'folder-empty', 'folder-unempty', 'fromchromefolder', 'documentfolder', 'fromphonefolder', 'mix', 'musicfolder', 'picturefolder', 'videofolder', 'sefolder', 'access', 'mdb', 'accdb', 'sql', 'c', 'cpp', 'cs', 'js', 'fla', 'flv', 'htm', 'html', 'java', 'log', 'mht', 'php', 'url', 'xml', 'ai', 'bmp', 'cdr', 'gif', 'ico', 'jpeg', 'jpg', 'JPG', 'png', 'psd', 'webp', 'ape', 'avi', 'flv', 'mkv', 'mov', 'mp3', 'mp4', 'mpeg', 'mpg', 'rm', 'rmvb', 'swf', 'wav', 'webm', 'wma', 'wmv', 'doc', 'docm', 'dotx', 'dotm', 'dot', 'rtf', 'docx', 'pdf', 'fdf', 'ppt', 'pptm', 'pot', 'potm', 'pptx', 'txt', 'xls', 'csv', 'xlsm', 'xlsb', 'xlsx', '7z', 'gz', 'cab', 'iso', 'rar', 'zip', 'bt', 'file', 'apk', 'css'];
    var extLastName = extArr[extArr.length - 1];
    for (var i = 0; i < exts.length; i++) {
        if (exts[i] == extLastName) {
            return exts[i];
        }
    }
    return 'file';
}
// 请求封装
function send(obj) {
    var loadT = '';
    if (obj.load == undefined) obj.load = 0;
    if (obj.url == undefined) {
        if (obj.plugin_name === undefined && this.plugin_name !== undefined) obj.plugin_name = this.plugin_name
        if (!obj.plugin_name || !obj.method) {
            layer.msg('The plugin class name, or plugin method name is missing!', {
                icon: 2
            });
            return false;
        }
    }
    if (obj.load === 0) {
        loadT = layer.msg(obj.tips, {
            icon: 16,
            time: 0,
            shade: 0.3
        });
    } else if (obj.load === 1 || (obj.tips == undefined && obj.load == undefined)) {
        loadT = layer.load();
    }
    $.ajax({
        type: 'POST',
        url: obj.url != undefined ? obj.url : ('/plugin?action=a&name=' + obj.plugin_name + '&s=' + obj.method),
        data: obj.data || {},
        timeout: obj.timeout || 99999999,
        complete: function (res) {
            if (obj.load === 0 || obj.load === 1) layer.close(loadT);
        },
        success: function (rdata) {
            if (!obj.success) {
                obj.msg || obj.msg == undefined ? layer.msg(rdata.msg, {
                    icon: rdata.status ? 1 : 2
                }) : '';
                return;
            }
            obj.success(rdata);
        },
        error: function (ex) {
            if (!obj.error) {
                obj.msg || obj.msg == undefined ? layer.msg('Request process found error!', {
                    icon: 2
                }) : '';
                return;
            }
            return obj.error(ex);
        }
    });
}

function SetChmod(action, fileName, is_files) {
    var is_file=false,
    backups = true,
    toExec = fileName == lan.files.all ? 'Batch(3,1)' : 'SetChmod(1,\'' + fileName + '\')',
    tex = '<div class="info-title-tips" style="padding-left: 7px;margin: 19px 23px;">\
                <span class="glyphicon glyphicon-alert" style="color: #f39c12; margin-right: 5px;"></span>\
                <span class="backuptip"></span>\
                <button class="restore btn btn-success btn-sm" onclick="backup(\'' + fileName + '\',1)" style="margin-left: 5px;">Backup</button>\
    			<div style="display: inline-block;width: 1px;height: 13px;background: #20a53a;vertical-align: middle;margin: 0 5px;"></div>\
				<button class="manage btn btn-default btn-sm tolist" style="padding:6px;">Restore</button>\
            </div>';
    if(is_files) is_file = is_files;
	this.send({
        url: '/files?action=GetFileAccess',
        tips: 'Getting permission, please wait...',
        data: {
            filename: fileName
        },
		success: function (rdata) {
        var layers = layer.open({
            type: 1,
            closeBtn: 2,
            btn: [lan.public.ok, lan.public.close],
            title: lan.files.set_auth + '[' + fileName + ']',
            area: ['477px','399px'],
            shadeClose: false,
            content: '<div class="setchmod bt-form" style="padding: 0;">\
            			<div class="bt_tab_list">\
				            <div class="bt_tab_index active" data-index="0">Set permission</div>\
				            <div class="bt_tab_index baclist" data-index="1" onclick="backup_file(\'' + fileName + '\')">Backups list</div>\
				        </div>\
                        <div class="chmodset">' + tex + '\
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
							</select></span>\
	                        <span><input type="checkbox" id="accept_all" ' + (is_file ? "checked" : "") + ' style="vertical-align: text-bottom;"/><label for="accept_all" style="margin-left: 5px;font-weight: 400;">' + lan.files.apply_to_subd + '</label></span>\
	                        </div>\
	                    </div>\
	                    <div class="backup_lists"></div>\
					</div>',
			yes: function (layers, index) {
				get_backup_file(fileName,function (edata) {
					if(edata.length == 0){
						$('.backuptip').text('No backup');
						backups = false;
					}
					setpromise(1, fileName, backups, is_file);
			    });
            },
            success: function (layers, index) {
                $('.layer_close').click(function () {
                    layer.close(index);
                });
            }
        });
        $(".tolist").click(function () {
            $(".baclist").click();
        });
        get_backup_file(fileName,function (edata) {
			if(edata.length == 0) $('.backuptip').text('No backup');
		});
        setCookie('layers', layers);

        onAccess();
        $("#access").keyup(function () {
            onAccess();
        });
        $(".bt_tab_list .bt_tab_index").click(function () {
            $(this).addClass('active').siblings().removeClass('active');
            if($(this).index()==0){
            	$('.backup_lists').empty();
            	$('.chmodset').show();
            }
        });

        $("input[type=checkbox]").change(function () {
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
		}
    })

}
function setpromise(action,fileName,backups,files){
    var is_files = files?files:false;
	if(fileName == lan.files.all){
		Batch(3,1)
	} else {
		if (action == 1) {
	        var chmod = $("#access").val(),
	        chown = $("#chown").val(),
	        all = $("#accept_all").prop("checked") ? 'True' : 'False',
	        data = 'filename=' + encodeURIComponent(fileName) + '&user=' + chown + '&access=' + chmod + '&all=' + all,
	        is_file = is_files ? 3 : 1;
	        if (!backups && all == 'True' && is_file == 3) {
	            var loadTips = layer.open({
	                type: 1,
	                closeBtn: 2,
	                title: 'Confirm backup',
	                area: '430px',
	                shadeClose: false,
	                btn: ['Apply&Backup', 'Cancel', 'Apply'],
	                content: '<div class="pd20" style="font-size: 13px;">Do you want to apply settings and back up permissions?\
	                                <div>Remarks\
	                                    <input type="text" class="form-control ml5 mt10" placeholder="Please enter name" style="font-size: 13px;width: 230px;display: inline-block;">\
	                                </div>\
	                            </div>',
	                success: function () {
	                    $('.layui-layer-btn2').css({
	                        "float": "left",
	                        "margin-left": "0"
	                    });
	                },
	                yes: function () {
	                    $('.layer_close').click(function () {
	                        layer.close(loadTips);
	                    });
	                    $.post('/files?action=back_path_permissions', {
	                        back_sub_dir: (all == 'True') ? 1 : 0,
	                        path: fileName,
	                        remark: $("input.form-control").val()
	                    }, function (edata) {
	                        var wrong = edata.status == false ? 2 : 1;
	                        layer.msg(edata.msg, {
	                            time: 1900,
	                            icon: wrong,
	                        });
	                        if (wrong == 2) {
	                            return false;
	                        }
	                        Oksend(data);
	                        layer.closeAll();
	                    });
	                },
	                btn2: function () {
	                    layer.close(loadTips);
	                },
	                btn3: function () {
	                    var loadT = layer.msg(lan.public.config, {
	                        icon: 16,
	                        time: 0,
	                        shade: [0.3, '#000']
	                    });
	                    Oksend(data, loadT);
	                    return;
	                },
	                cancel: function () {
	                    layer.close(loadTips);
	                }
	            });
	            return;
	        } else {
	            var loadT = layer.msg(lan.public.config, {
	                icon: 16,
	                time: 0,
	                shade: [0.3, '#000']
	            });
	            Oksend(data, loadT);
	            return;
	        }
	    }
	}
}
// 获取备份列
function get_backup_file(obj,callback){
    this.send({
        url: '/files?action=get_path_premissions',
        tips: 'Getting file list, please wait...',
        data: {
            path: obj
        },
        success: function (res) {
            if (callback) callback(res);
        }
    });
}
// 修复权限
function fix_permissions(obj,callback){
    this.send({
        url: '/files?action=fix_permissions',
        tips: 'Getting file list, please wait...',
        data: {
            path: obj
        },
        success: function (res) {
            if (callback) callback(res);
            layer.closeAll();
            layer.msg(res.msg, { icon: res.status ? 1 : 2 });
        }
    });
}
//本文件备份列表
function backup_file(fileName) {
	get_backup_file(fileName,function (edata) {
		var tbody = '',cont='';
		if(edata.length==0){
			tbody='<tr><td colspan="5" align="center">No data</td></tr>'
		}else{
	    	for (var i = 0; i < edata.length; i++) {
	    		var d = new Date(edata[i][3] * 1000),
	    		minut = d.getMinutes(),
	    		hours = d.getHours();
	            if (minut <= 9) minut = '0' + minut + '';
	            if (hours <= 9) hours = '0' + hours + '';
	            var date = (d.getFullYear()) + "/" +
	                (d.getMonth() + 1) + "/" +
	                (d.getDate()) + " " +
	                (hours) + ":" +
	                (minut);
		    	tbody += '<tr>\
	                <td><span style="display: inline-block;width: 60px; overflow: hidden;text-overflow: ellipsis;">'+edata[i][4]+'</span></td>\
	                <td>'+edata[i][2]+'</td>\
	                <td>'+edata[i][1]+'</td>\
	                <td>'+date+'</td>\
	                <td style="color: #666;"><a onclick="restore(' + edata[i][3] + ')" class="btlink">Restore</a> | <a onclick="delback(' + edata[i][5] + ')" class="btlink">Del</a></td>\
	            </tr>';
	    	}
		}
    	cont = '<div class="divtable" style="height: 260px; overflow: auto;padding:11px 13px 3px;">\
    		<div class="info-title-tips" style="text-align:left;margin-bottom: 7px;">\
                <span class="glyphicon glyphicon-alert" style="color: #f39c12; margin-right: 5px;"></span>\
                <span>Fix all permissions to [ Folder: 755, File: 644 ]</span>\
				<button class="manage btn btn-default btn-sm btn-success fixper" style="padding:6px;margin-left: 7px;">Fix permissions</button>\
			</div>\
    		<table width="100%" border="0" cellpadding="0" cellspacing="0" class="table table-hover">\
                <thead>\
                    <tr>\
                        <th width="60">Name</th>\
                        <th width="35">permission</th>\
                        <th width="45">Owner</th>\
                        <th>Backup Time</th>\
                        <th width="80">options</th>\
                    </tr>\
                </thead>\
                <tbody class="backup_list">\
                	'+tbody+'\
                </tbody>\
            </table>\
        </div>';
        $('.chmodset').hide();
        $('.backup_lists').html(cont);
        $(".fixper").click(function () {
        	layer.confirm('Note: Under the file or folder all permissions will be fixed to [ Folder: 755, File: 644 ]',{title: 'Fix Permissions？',btn: ['Confirm', 'Cancel'],closeBtn:2},function(index, layero){
            	fix_permissions(fileName);
            	var path = $("#DirPathPlace input").val();
            	GetFiles(path);
            });
        });
    });
}

function onAccess() {
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
}

function RClick(type, path, name, file_store, file_share,data_composer) {
    var displayZip = isZip(type);
    var options = {
        items: [{
                text: lan.files.file_menu_copy,
                onclick: function () {
                    CopyFile(path)
                }
            },
            {
                text: lan.files.file_menu_mv,
                onclick: function () {
                    CutFile(path)
                }
            },
            {
                text: lan.files.file_menu_rename,
                onclick: function () {
                    ReName(0, name)
                }
            },
            {
                text: lan.files.file_menu_auth,
                onclick: function () {
                    SetChmod(0, path)
                }
            },
            {
                text: lan.files.file_menu_zip,
                onclick: function () {
                    Zip(path)
                }
            }
        ]
    };

    if (type == "dir") {
        options.items.push({
            text: lan.files.file_menu_del,
            onclick: function () {
                DeleteDir(path)
            }
        }, 
        // {
        //     text: lan.files.dir_menu_webshell,
        //     onclick: function () {
        //         webshell_dir(path)
        //     }
        // }
        );
    } else if (isPhp(type)) {
        options.items.push({
            text: lan.files.file_menu_webshell,
            onclick: function () {
                php_file_webshell(path)
            }
        }, {
            text: lan.files.file_menu_edit,
            onclick: function () {
                openEditorView(0, path)
            }
        }, {
            text: lan.files.file_menu_down,
            onclick: function () {
                GetFileBytes(path)
            }
        }, {
            text: lan.files.file_menu_del,
            onclick: function () {
                DeleteFile(path)
            }
        })
    }
    else if (isVideo(type)) {
        options.items.push({ text: 'Play', onclick: function () { GetPlay(path) } }, { text: lan.files.file_menu_down, onclick: function () { GetFileBytes(path) } }, { text: lan.files.file_menu_del, onclick: function () { DeleteFile(path) } });
    }
    else if (isText(type)) {
        options.items.push({
            text: lan.files.file_menu_edit,
            onclick: function () {
                openEditorView(0, path)
            }
        }, {
            text: lan.files.file_menu_down,
            onclick: function () {
                GetFileBytes(path)
            }
        }, {
            text: lan.files.file_menu_del,
            onclick: function () {
                DeleteFile(path)
            }
        });
    } else if (displayZip != -1) {
        options.items.push({
            text: lan.files.file_menu_unzip,
            onclick: function () {
                UnZip(path, displayZip)
            }
        }, {
            text: lan.files.file_menu_down,
            onclick: function () {
                GetFileBytes(path)
            }
        }, {
            text: lan.files.file_menu_del,
            onclick: function () {
                DeleteFile(path)
            }
        });
    } else if (isImage(type)) {
        options.items.push({
            text: lan.files.file_menu_img,
            onclick: function () {
                GetImage(path)
            }
        }, {
            text: lan.files.file_menu_down,
            onclick: function () {
                GetFileBytes(path)
            }
        }, {
            text: lan.files.file_menu_del,
            onclick: function () {
                DeleteFile(path)
            }
        });
    } else {
        options.items.push({
            text: lan.files.file_menu_down,
            onclick: function () {
                GetFileBytes(path)
            }
        }, {
            text: lan.files.file_menu_del,
            onclick: function () {
                DeleteFile(path)
            }
        });
    }
    // if (type !== 'dir') {
    //     options.items.push({
    //         text: 'Share',
    //         onclick: function () {
    //             create_download_url(name, path, file_share)
    //         }
    //     });
    // }
    // if(type !== 'dir'){
    //     options.items.push({ text: 'Share', onclick: function () { create_download_url(name,path,file_share) } });
    // }

    options.items.push({ text: 'Share', onclick: function () {
        create_download_url(name,path,file_share) } });

    if( type === 'dir' && data_composer === '1'){
        options.items.push({ text: 'Composer', onclick: function () { exec_composer(name,path) } });
    }

    options.items.push({
        text: "Favorites",
        onclick: function () {
            var loading = bt.load();
            bt.send('add_files_store', 'files/add_files_store', {
                path: path
            }, function (rRet) {
                loading.close();
                bt.msg(rRet);
                if (rRet.status) {
                    console.log(file_store.PATH);
                    GetFiles(file_store.PATH)
                }
            });
        }
    })
    return options;
}

function update_composer(){
    loadT = bt.load()
    $.post('/files?action=update_composer',{},function(v_data){
        loadT.close();
        bt.msg(v_data);
    });
}

function exec_composer(fileName,path){
    $.post('/files?action=get_composer_version',{},function(v_data){
        if(v_data.status === false){
            bt.msg(v_data);
            return;
        }

        var php_versions = '';
        for(var i=0;i<v_data.php_versions.length;i++){
            if(v_data.php_versions[i].version == '00') continue;
            php_versions += '<option value="'+v_data.php_versions[i].version+'">'+v_data.php_versions[i].name+'</option>';
        }

        var layers = layer.open({
            type: 1,
            closeBtn: 2,
            area: '450px',
            title: 'Execute composer in ['+path+'] directory',
            btn:['Composer','Cancel'],
            content: '<from class="bt-form" style="padding:30px 15px;display:inline-block">'
                + '<div class="line"><span class="tname">Edition</span><div class="info-r"><input readonly="readonly" style="background-color: #eee;" name="composer_version" class="bt-input-text" value="'+v_data.msg +'" /><a onclick="update_composer();" style="margin-left: 5px;" class="btn btn-default btn-sm">Update composer<a></div></div>'
                + '<div class="line"><span class="tname">PHP Edition</span><div class="info-r">'
                    +'<select class="bt-input-text" name="php_version">'
                        +'<option value="auto">Auto select</option>'
                        +php_versions
                    +'</select>'
                +'</div></div>'
                + '<div class="line"><span class="tname">Parameter</span><div class="info-r">'
                    +'<select class="bt-input-text" name="composer_args">'
                        +'<option value="install">Install</option>'
                        +'<option value="update">Update</option>'
                    +'</select>'
                +'</div></div>'
                + '<div class="line"><span class="tname">Mirror source</span><div class="info-r">'
                    +'<select class="bt-input-text" name="repo">'
                        +'<option value="https://mirrors.aliyun.com/composer/">Ali：mirrors.aliyun.com</option>'
                        +'<option value="repos.packagist">Official：packagist.org</option>'
                    +'</select>'
                +'</div></div>'
                + '</from>',
            yes:function(indexs,layers){
                layer.confirm('The scope of influence of executing composer depends on the composer.json configuration file in this directory.Continue？', { title: 'Confirm Composer?',btn:['Confirm','Cancel'], closeBtn: 2, icon: 3 }, function (index) {
                    var pdata = {
                        php_version:$("select[name='php_version']").val(),
                        composer_args:$("select[name='composer_args']").val(),
                        repo:$("select[name='repo']").val(),
                        path:path
                    }
                    $.post('/files?action=exec_composer',pdata,function(rdatas){
                        if(!rdatas.status){
                            layer.msg(rdatas.msg,{icon:2});
                            return false;
                        }
                        layer.closeAll();
                        if(rdatas.status === true){
                            layer.open({
                                area:"600px",
                                type: 1,
                                shift: 5,
                                closeBtn: 2,
                                title: 'Execute composer in ['+path+'] directory, and close this window after execution',
                                content:"<pre id='composer-log' style='height: 300px;background-color: #333;color: #fff;margin: 0 0 0;'></pre>"
                            });
                            setTimeout(function(){show_composer_log();},200);
                        }
                    });
                });
            }
        });
    });
}


function show_composer_log(){
    $.post('/ajax?action=get_lines',{filename:'/tmp/panelExec.pl',num:30},function(v_body){
        var log_obj = $("#composer-log")
        if(log_obj.length < 1) return;
        log_obj.html(v_body.msg);
        var div = document.getElementById('composer-log')
        div.scrollTop = div.scrollHeight;
        setTimeout(function(){show_composer_log()},1000)
    });
}


function create_download_url(fileName, path, fileShare) {
    fileShare = parseInt(fileShare);
    if(fileShare != 0) {
        $.post('/files?action=get_download_url_find', {
            id: fileShare
        }, function (rdata) {
            set_download_url(rdata);
        });
        return false
    }
    var layers = layer.open({
        type: 1,
        shift: 5,
        closeBtn: 2,
        area: '450px',
        title: 'Share details',
        btn: ['Create', 'Cancel'],
        content: '<from class="bt-form" id="outer_url_form" style="padding:30px 15px;display:inline-block">' +
            '<div class="line"><span class="tname">Sharing name</span><div class="info-r"><input name="ps" class="bt-input-text mr5" type="text" placeholder="No sharing name" style="width:270px" value="' + fileName + '"></div></div>' +
            '<div class="line"><span class="tname">Term of validity</span><div class="info-r">' +
            '<label class="checkbox_grourd"><input type="radio" name="expire" value="24" checked><span>&nbsp;a day</span></label>' +
            '<label class="checkbox_grourd"><input type="radio" name="expire" value="168"><span>&nbsp;a week</span></label>' +
            '<label class="checkbox_grourd"><input type="radio" name="expire" value="99999999"><span>&nbsp;permanent</span></label>' +
            '</div></div>' +
            '<div class="line"><span class="tname">Extraction code</span><div class="info-r"><input name="password" class="bt-input-text mr5" placeholder="No code if it is empty" type="text" style="width:170px" value=""><button type="button" id="random_paw" class="btn btn-success btn-sm btn-title">Random</button></div></div>' +
            '</from>',
        yes: function (indexs, layers) {
            layer.confirm('Confirm to share this file？', {
                title: 'Sharing',
                closeBtn: 2,
                icon: 3
            }, function (index) {
                var ps = $('[name=ps]').val(),
                    expire = $('[name=expire]').val(),
                    password = $('[name=password]').val();
                if (ps === '') {
                    layer.msg('No sharing name', {
                        icon: 2
                    });
                    return false;
                }
                $.post('/files?action=create_download_url', {
                    filename: path,
                    ps: ps,
                    password: password,
                    expire: expire
                }, function (rdatas) {
                    if (!rdatas.status) {
                        layer.msg(rdatas.msg, {
                            icon: 2
                        });
                        return false;
                    }
                    layer.close(index);
                    layer.close(indexs)
                    set_download_url(rdatas.msg);
                });
            });
        },
        success: function (layers, index) {
            $('#random_paw').click(function () {
                $(this).prev().val(bt.get_random(6));
            });
        }
    });
}


function set_download_url(rdata) {
    var download_url = window.location.protocol + '//' + window.location.host + '/down/' + rdata.token;
    var layers = layer.open({
        type: 1,
        shift: 5,
        closeBtn: 2,
        area: '550px',
        title: 'Share details',
        content: '<div class="bt-form pd20 pb70">'
	            + '<div class="line"><span class="tname">Name</span><div class="info-r"><input readonly class="bt-input-text mr5" type="text" style="width:365px" value="'+ rdata.ps +'"></div></div>'
	        	+ '<div class="line external_link"><span class="tname">Share address</span><div class="info-r"><input readonly class="bt-input-text mr5" type="text" style="width:280px" value="'+ download_url +'"><button type="button" id="copy_url" data-clipboard-text="'+ download_url +'" class="btn btn-success btn-sm btn-title copy_url" style="margin-right:5px" data-clipboard-target="#copy_url"><img style="width:16px" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAABIUlEQVQ4T6XTsSuFURjH8d+3/AFm0x0MyqBEUQaUIqUU3YwWyqgMptud/BlMSt1SBiklg0K3bhmUQTFZDZTxpyOvznt7z3sG7/T2vOf5vM85z3nQPx+KfNuHkhoZ7xXYjNfEwIukXUnvNcg2sJECnoHhugpsnwBN21PAXVgbV/AEjNhuVSFA23YHWLNt4Cc3Bh6BUdtLcbzAgHPbp8BqCngAxjJbOANWUkAPGA8fE8icpD1gOQV0gclMBRfAYgq4BaZtz/YhA5IGgY7tS2AhBdwAM7b3JX1I+iz1G45sXwHzKeAa6P97qZgcEA6v/ZsR3v9aHCmt0P9UBVuShjKz8CYpXPkDYKJ0kaKhWpe0UwOFxDATx5VACFZ0Ivbuga8i8A3NFqQRZ5pz7wAAAABJRU5ErkJggg=="></button><button type="button" class="btn btn-success QR_code btn-sm btn-title"><img  style="width:16px" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAABUklEQVQ4T6WSIU9DQRCEvwlYLIoEgwEECs3rDyCpobbtL6AKRyggMQ9TJBjUMzgMCeUnIEAREoICFAoEZMk2dy/Xo4KGNZu7nZ2bnT3xz1DsN7MFYCnhe5V0n/Kb2QowL2kY70cEoXAHVEnDG/ABXAJXmVDHVZKqSFAA58AqsAY8AW3A68/AQ7hbBG6BbeDGlaQEh8AucA3suzDgC5gFXHID2At5YxJBNwA6ocFBM8B3OL8DTaCcpMDN2QojxHHdk9Qrx9SeAyf1CMFIJ3DjYqxLOgo192gs4ibSNfrMOaj2yBvMrCnpImYHR4C/vizpIPkX/mpbUtfMepJKMxtKKsyslNTLCZxkBzgFjoE5oCVp08yKvyhwgkGyRl9nX1LDzDz3kzxS8kuBpFYygq8xJ4gjjBMEpz+BF+AxcXLg39XMOpLOciW1gtz9ac71GqdpSrE/8U20EQ3XLHEAAAAASUVORK5CYII="></button></div></div>'
	        	+ '<div class="line external_link" style="'+ (rdata.password == ""?"display:none;":"display:block") +'"><span class="tname">Extraction code</span><div class="info-r"><input readonly class="bt-input-text mr5" type="text" style="width:243px" value="'+ rdata.password +'"><button type="button" data-clipboard-text="link:'+ download_url +' Extraction code:'+ rdata.password +'"  class="btn btn-success copy_paw btn-sm btn-title">Copy link and code</button></div></div>'
	        	+ '<div class="line"><span class="tname">Expiration date</span><div class="info-r"><span style="line-height:32px; display: block;font-size:14px">'+ bt.format_data(rdata.expire)+'</span></div></div>'
	        	+ '<div class="bt-form-submit-btn">'
	            + '<button type="button" class="btn btn-danger btn-sm btn-title layer_close">' + lan.public.close + '</button>'
	            + '<button type="button" id="down_del" class="btn btn-danger btn-sm btn-title close_down" style="color:#fff;background-color:#c9302c;border-color:#ac2925;" onclick="">Close sharing chain</button>'
	            + '</div>'
            + '</div>',
        success: function (layers, index) {
            var copy_url = new ClipboardJS('.copy_url');
            var copy_paw = new ClipboardJS('.copy_paw');
            copy_url.on('success', function (e) {
                layer.msg('Copy link succeeded!', {
                    icon: 1
                });
                e.clearSelection();
            });
            copy_paw.on('success', function (e) {
                layer.msg('Copy extraction code succeeded!', {
                    icon: 1
                });
                e.clearSelection();
            });
            $('.layer_close').click(function () {
                layer.close(index);
            });
            $('.QR_code').click(function () {
                layer.closeAll('tips');
                layer.tips('<div style="height:140px;width:140px;padding:8px 0" id="QR_code"></div>', '.QR_code', {
                    area: ['150px', '150px'],
                    tips: [1, '#ececec'],
                    time: 0,
                    shade: [0.05, '#000'],
                    shadeClose: true,
                    success: function () {
                        jQuery('#QR_code').qrcode({
                            render: "canvas",
                            text: download_url,
                            height: 130,
                            width: 130
                        });
                    }
                });
            });
            $('.close_down').click(function () {
                del_download_url(rdata.id, index)
            });
        }
    });
}

function del_download_url(id, indexs) {
    layer.confirm('Confirm cancel sharing the file？', {
        title: 'Confirm',
        closeBtn: 2,
        icon: 3
    }, function (index) {
        $.post('/files?action=remove_download_url', {
            id: id
        }, function (res) {
            layer.msg(res.msg, {
                icon: res.status ? 1 : 2
            });
            layer.close(indexs);
            layer.close(index);
            if (indexs === false) get_download_url_list({}, true);
        });
    });
}

function get_download_url_list(data, is_refresh) {
    if (data == undefined) data = {
        p: 1
    }
    $.post('/files?action=get_download_url_list', {
        p: data.p
    }, function (res) {
        var _html = '',
            rdata = res.data;
        for (var i = 0; i < rdata.length; i++) {
            _html += '<tr><td>' + rdata[i].ps + '</td><td>' + rdata[i].filename + '</td><td>' + bt.format_data(rdata[i].expire) + '</td><td style="text-align:right;"><a href="javascript:;" class="btlink info_down" data-index="' + i + '" data-id="' + rdata[i].id + '">Detail</a>&nbsp;&nbsp;|&nbsp;&nbsp;<a href="javascript:;" class="btlink del_down" data-id="' + rdata[i].id + '" data-index="' + i + '">Close</a></td></tr>';
        }
        if (is_refresh) {
            $('.download_url_list').html(_html);
            $('.download_url_page').html(res.page);
            return false;
        }
        var layers = layer.open({
            type: 1,
            shift: 5,
            closeBtn: 2,
            area: ['850px', '580px'],
            title: 'Share list',
            content: '<div class="divtable mtb10 download_table" style="padding:5px 10px;">\
    <table class="table table-hover" id="download_url">\
        <thead><tr><th>Sharing name</th><th>File address</th><th>Expiration date</th><th style="text-align:right;">Operation</th></tr></thead>\
        <tbody class="download_url_list">' + _html + '</tbody>\
    </table>\
    <div class="page download_url_page">' + res.page + '</div>\
</div>',
            success: function (layers, index) {
                $('.download_table').on('click', '.info_down', function () {
                    var indexs = $(this).attr('data-index');
                    set_download_url(rdata[indexs]);
                });
                $('.download_table').on('click', '.del_down', function () {
                    var id = $(this).attr('data-id');
                    del_download_url(id, false);
                });
                $('.download_table .download_url_page').on('click', 'a', function (e) {
                    var _href = $(this).attr('href');
                    var page = _href.replace(/\/files\?action=get_download_url_list\?p=/, '')
                    get_download_url_list({
                        p: page
                    }, true);
                    return false;
                });
            }
        });
    });
}


function RClickAll(e) {
    var menu = $("#rmenu");
    var windowWidth = $(window).width(),
        windowHeight = $(window).height(),
        menuWidth = menu.outerWidth(),
        menuHeight = menu.outerHeight(),
        x = (menuWidth + e.clientX < windowWidth) ? e.clientX : windowWidth - menuWidth,
        y = (menuHeight + e.clientY < windowHeight) ? e.clientY : windowHeight - menuHeight;

    menu.css('top', y)
        .css('left', x)
        .css('position', 'fixed')
        .css("z-index", "1")
        .show();
}

function GetPathSize() {
    var path = encodeURIComponent($("#DirPathPlace input").val());
    layer.msg(lan.files.calc_now, {
        icon: 16,
        time: 0,
        shade: [0.3, '#000']
    })
    $.post("/files?action=GetDirSize", "path=" + path, function (rdata) {
        layer.closeAll();
        $("#pathSize").text(rdata)
    })
}
$("body").not(".def-log").click(function () {
    $("#rmenu").hide()
});
$("#DirPathPlace input").keyup(function (e) {
    if (e.keyCode == 13) {
        GetFiles($(this).val());
    }
});

function PathPlaceBtn(path) {
    var html = '';
    var title = '';
    path = path.replace('//', '/');
    var Dpath = path;
    if (path == '/') {
        html = '<li><a title="/">' + lan.files.path_root + '</a></li>';
    } else {
        Dpath = path.split("/");
        for (var i = 0; i < Dpath.length; i++) {
            title += Dpath[i] + '/';
            Dpath[0] = lan.files.path_root;
            html += '<li><a title="' + title + '">' + Dpath[i] + '</a></li>';
        }
    }
    html = '<div style="width:1200px;height:26px"><ul>' + html + '</ul></div>';
    $("#PathPlaceBtn").html(html);
    $("#PathPlaceBtn ul li a").click(function (e) {
        var Gopath = $(this).attr("title");
        if (Gopath.length > 1) {
            if (Gopath.substr(Gopath.length - 1, Gopath.length) == '/') {
                Gopath = Gopath.substr(0, Gopath.length - 1);
            }
        }
        GetFiles(Gopath);
        e.stopPropagation();
    });
    PathLeft();
}

function PathLeft() {
    var UlWidth = $("#PathPlaceBtn ul").width();
    var SpanPathWidth = $("#PathPlaceBtn").width() - 50;
    var Ml = UlWidth - SpanPathWidth;
    if (UlWidth > SpanPathWidth) {
        $("#PathPlaceBtn ul").css("left", -Ml)
    } else {
        $("#PathPlaceBtn ul").css("left", 0)
    }
}

var store_type_index = 0
//删除分类或者文件
function del_files_store(path, obj) {
    var _item = $(obj).parents('tr').data('item')
    var action = '',
        msg = '';
    var data = {}
    action = 'del_files_store';
    data['path'] = _item.path;
    msg = "Are you sure to delete the path [ " + _item.path + " ]?"
    bt.confirm({
        msg: msg,
        title: 'Tips'
    }, function () {
        var loading = bt.load();
        bt.send(action, 'files/' + action, data, function (rRet) {
            loading.close();
            if (rRet.status) {
                set_file_store(path)
                GetFiles(getCookie('Path'))
            }
            bt.msg(rRet);
        })
    })
}

function set_file_store(path) {

    var loading = bt.load();
    bt.send('get_files_store', 'files/get_files_store', {}, function (rRet) {
        loading.close();
        if ($('#stroe_tab_list').length <= 0) {
            bt.open({
                type: 1,
                skin: 'demo-class',
                area: '510px',
                title: "Manage favorites",
                closeBtn: 2,
                shift: 5,
                shadeClose: false,
                content: "<div class='divtable pd15 style='padding-bottom: 0'><table width='100%' id='stroe_tab_list' class='table table-hover'></table><div class='page sitebackup_page'></div></div>",
                success: function () {
                    $('#btn_data_store_add').click(function () {
                        bt.send('add_files_store_types', 'files/add_files_store_types', {
                            file_type: $(".type_name").val()
                        }, function (rRet) {
                            loading.close();

                            if (rRet.status) {
                                set_file_store(path)
                                GetFiles(path)
                            }
                            bt.msg(rRet);
                        })
                    })
                    reload_sort_data(path)
                }
            });
        } else {
            reload_sort_data(path)
        }

        function reload_sort_data(path) {
            var _tab = bt.render({
                table: '#stroe_tab_list',
                columns: [{
                        field: 'path',
                        title: 'Path'
                    },
                    {
                        field: 'opt',
                        align: 'right',
                        title: 'Operation',
                        templet: function (item) {
                            return '<a class="btlink del_file_store" onclick="del_files_store(\'' + path + '\',this)" >Del</a>';
                        }
                    },
                ],
                data: rRet
            });
        }
    })
}



$("#PathPlaceBtn").on("click", function (e) {
    if ($("#DirPathPlace").is(":hidden")) {
        $("#DirPathPlace").css("display", "inline");
        $("#DirPathPlace input").focus();
        $(this).hide();
    } else {
        $("#DirPathPlace").hide();
        $(this).css("display", "inline");
    }
    $(document).one("click", function () {
        $("#DirPathPlace").hide();
        $("#PathPlaceBtn").css("display", "inline");
    });
    e.stopPropagation();
});
$("#DirPathPlace").on("click", function (e) {
    e.stopPropagation();
});