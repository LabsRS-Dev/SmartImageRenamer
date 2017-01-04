/**
 * Created by Ian on 2014/8/8.
 */

(function(){
    window['UI'] = window['UI'] || {};
    window.UI.c$ = window.UI.c$ || {};
})();


(function(){
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    var c$ = {};
    c$ = $.extend(window.UI.c$,{});

    /**
     * 初始化标题及版本
     */
    c$.initTitleAndVersion = function(){
        document.title = BS.b$.App.getAppName();
    };


    // 与Angular的Action的关联部分
    c$.link_AngularActionsInject = function($scope, $http, $translate,  $mdDialog){
        var b$ = BS.b$;


        // 设置选项默认值
        $scope.options = {
            'ddInputPath': '',
            'ddOutputPath': '',
            'ddFormat': '{YYYY}{DD}{MM}_Beach_Shoot_{Seq}',
            'recursive': false,
            'hide': false,
            'enableSequence':false,
            'overwrite':false,
            'deleteSource':false,
            'sequence':1
        };

        $scope.ddRenameDisabled = false;
        $scope.ddProgressHide = true;

        // 选择输入目录
        $scope.onSelectDir = function(){
            b$.selectOutDir({
                callback: b$._get_callback(function(obj){
                    if(obj.success){
                        var dir = obj.filesArray[0].filePath;
                        $scope.$apply(function () {
                            $scope.options.ddInputPath = dir;
                        });

                    }
                }, true),
                title: "Select Photos Directory",
                prompt: "Select"
            });
        };

        // 选择输出目录
        $scope.onSelectOutDir = function(){
            b$.selectOutDir({
                callback: b$._get_callback(function(obj){
                    if(obj.success){
                        var dir = obj.filesArray[0].filePath;
                        $scope.$apply(function () {
                            $scope.options.ddOutputPath = dir;
                        });
                    }
                }, true),
                title: "Select Output Directory",
                prompt: "Select"
            });
        };

        $scope.onClickLog = function(ev){
            $scope.messages = [];
        };


        $scope.onClickRename = function(ev){
            var ui_inputPath = $.trim($scope.options.ddInputPath);
            var ui_outputPath = $.trim($scope.options.ddOutputPath);
            var cf = b$.App.checkPathIsExist;
            if($.isMac){
                if(ui_inputPath.length == 0 || cf(ui_inputPath) == false) return $scope.onSelectDir();
                if(ui_outputPath.length == 0 || cf(ui_outputPath) == false) return $scope.onSelectOutDir();
            }else{
                if(ui_inputPath.length == 0) ui_inputPath = 'D:/temp/img';
                if(ui_outputPath.length == 0) ui_outputPath = 'D:/temp/img_out';
            }

            // 格式化内容不能空值
            if($.trim($scope.options.ddFormat).length < 1){
                $scope.options.ddFormat = '{YYYY}{DD}{MM}_Beach_Shoot_{Seq}';
                return alert("The format content can't empty!")
            }

            // 如果输入和输出相同，弹出警告，并显示会直接覆盖
            if(ui_inputPath === ui_outputPath){
                var confirm = $mdDialog.confirm()
                    .title('Without backup?')
                    .content('The same input and output directories. \n ' +
                    'Would you like to rename the file directly, without backup? \n' +
                    'You can re-select the output directory or without backup.')
                    .ariaLabel('SameDir')
                    .ok('Okay')
                    .cancel('Re-select')
                    .targetEvent(ev);
                $mdDialog.show(confirm).then(function() {
                    commandCall();
                }, function() {
                    $scope.onSelectOutDir();
                });
            }else{
                commandCall();
            }

            // 核心处理代码
            function commandCall(){
                var seq = 1;
                if ($scope.options.enableSequence) seq = $scope.options.sequence;


                var command = [
                    '-o', ui_outputPath
                    , '-f', $scope.options.ddFormat
                    , '-s', String(seq)
                ];

                $scope.options.recursive ? command.push('-r'): null;
                $scope.options.hide ? command.push('-i'): null;
                $scope.options.overwrite ? command.push('-w'): null;
                $scope.options.deleteSource ? command.push('-d'): null;
                command.push(ui_inputPath);

                c$.pythonAddon.common_service('ExifImageRenamer',
                    command,
                    c$.pythonAddon.getNewCallbackName(function(obj){

                        if(obj.type == 'python_task_running'){
                            $scope.$apply(function ($scope) {
                                $scope.ddProgressHide = false;
                                $scope.ddRenameBtnDisabled = true;
                            });

                            var log = $.getMyDateStr() +'  ' + 'start...';
                            $scope.messages.push({face:'images/time_16.png', detail:log});
                        }else if(obj.type == 'python_task_finished'){

                            $scope.$apply(function ($scope) {
                                $scope.ddProgressHide = true;
                                $scope.ddRenameBtnDisabled = false;
                            });


                            var result = obj.data.result;
                            var processedMapFiles = result['processed'];
                            var skippedMapFiles = result['skipped'];

                            $translate('log-rename-total-info',
                                {processedCount:processedMapFiles.length, skippedCount:skippedMapFiles.length}).then(function(message){
                                    $.each(skippedMapFiles, function(i, skippedFile){
                                        var log = skippedFile['file'] + '(' + skippedFile['error'] + ')';
                                        $scope.messages.push({face:'images/pass_16.png', detail:log})
                                    });
                                    $.each(processedMapFiles, function(i, mapFiles){
                                        var log = mapFiles['old'] + ' ---> ' + mapFiles['new'];
                                        $scope.messages.push({face:'images/yes_16.png', detail:log})
                                    });
                                    var log = $.getMyDateStr() +'  ' + message;
                                    $scope.messages.push({face:'images/time_16.png', detail:log});

                                });

                            $translate('msg-process-success').then(function(message){
                                alert(message);
                            });
                        }else if(obj.type == 'python_task_error'){
                            $scope.$apply(function ($scope) {
                                $scope.ddProgressHide = true;
                                $scope.ddRenameBtnDisabled = false;
                            });

                            var message = {
                                title:"Error",
                                message:obj.error,
                                buttons:["OK"],
                                alertType:"Alert"
                            };
                            b$.Notice.alert(message);
                        }else {
                            $scope.$apply(function ($scope) {
                                $scope.ddRenameBtnDisabled = false;
                            });

                        }

                    },true)
                );
            }

        };

        $scope.onShowHelp = function(ev){
            $mdDialog.show({
                controller: DialogController,
                templateUrl: 'views/dialog.help.html',
                targetEvent: ev
            })
        };

        function DialogController($scope, $mdDialog) {
            $scope.hide = function() {
                $mdDialog.hide();
            };
            $scope.cancel = function() {
                $mdDialog.cancel();
            };
            $scope.answer = function(answer) {
                $mdDialog.hide(answer);
            };
        }


        $scope.languageChange = function(x){
            console.log(x);
        };

        // UI语言部分处理
        $scope.uiLanguageChange = function(x){
            console.log(x);
            $translate.use(x);
        };

        $http({
            method: 'GET',
            url:'data/ui_language_opt.json'
        }).success(function(data){
            $scope.uiLanguageList = data;
            $scope.uiLanguage = $translate.use();
        });

        var passPng = 'images/pass_16.png';
        var yesPng = 'images/yes_16.png';
        $scope.messages = [
             //{face:yesPng,detail:'2015-1-16 10:00:31 {YYYY}{DD}{MM}_{Model}_Beach_Shoot_{Seq} 20140429_PENTAX K-x_Beach_Shoot_001.JPEG)'}
        ]
    };


    // 初始化UI
    c$.go = function(){
        // 启动Python服务器
        c$.python.registerPyWSMessageCB(function(data){
            var jsonObj = JSON.parse(data);
            var msgType = jsonObj['msg_type'];

            //
            if(msgType == 's_get_id_Info'){
                console.info('server getting the client id');
                c$.jCallback.fire({type:'python_server_get_id_info', data:{}});
            }

            // 核心处理部分
            if(msgType == 's_task_exec_running'){
                c$.jCallback.fire({type:'python_task_running',data:jsonObj})
            }else if(msgType == 's_task_exec_result'){
                c$.jCallback.fire({type:'python_task_finished',data:jsonObj})
            }else if(msgType == 's_err_progress'){
                c$.jCallback.fire({type:'python_task_error', data:jsonObj, error:jsonObj.content})
            }

        });
        c$.python.startPyWebServer();
    };

    // 回调处理函数
    c$.jcallback_process = function(obj){
        var fireType = obj.type;

        // Python的处理部分，将转移到各自的回调函数中
        if(fireType.indexOf('python_',0) > -1){
            console.log('##RecivePythonMessage:\n' + $.obj2string(obj));
            try{
                var callback = obj.data['cb'];
                if (typeof callback != 'undefined' && callback.length > 0){
                    var jsString = callback + '(obj)';
                    try{
                        eval(jsString)
                    }catch(e){console.error(e)}
                }
            }catch(e){}
        }

        ///本地内置任务部分
        if(fireType == '_native_task_added'){

        }else if(fireType == '_native_task_started'){
            // 检查PythonServer服务是否正常开启
            var queueID = obj.data.queueInfo.id;
            var reg = new RegExp('^' + c$.global.PyServerPrefix +'','i');
            if (reg.test(queueID)){
                setTimeout(function(){
                    c$.python.createPyWS();
                },3500);
            }

        }else if(fireType == '_native_task_error'){

        }else if(fireType == '_native_task_finished'){

        }else if(fireType == '_native_task_canceled'){

        }

    };


    window.UI.c$ = $.extend(window.UI.c$,c$);

})();





