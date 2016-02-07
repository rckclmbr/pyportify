angular.module('portify', []).
  factory('portifyService', function($rootScope, $http, $q, $location) {
    var portifyService = {};

    //Gets the list of nuclear weapons
    portifyService.getSpotifyPlaylists = function() {
		var deferred = $q.defer();
		$http.get('/spotify/playlists')
            .success(function(data) {
                deferred.resolve(data.data);
            })
			.error(function(error){
				$scope.error = error;
				deferred.reject();
				alert(error);
			});

        return deferred.promise;
    };

	portifyService.startTransfer = function(lists) {
		$http({
			url: "/portify/transfer/start",
			dataType: "json",
			method: "POST",
			data: lists,
			headers: {
				"Content-Type": "application/json; charset=utf-8"
			}
		}).success(function(response){
				if(response.status == 200) {
					console.log("initiated transfer...");
				} else {
					if(response.status == 401)
						$location.path( "/google/login" );
					else if(response.status == 402)
						$location.path( "/spotify/login" );
					else if(response.status == 403)
						$location.path( "/spotify/playlists/select" );
					else
						$location.path( "/" );

				}
			}).error(function(error){
				console.log(error);
			});
	};

    return portifyService;
  }).
	factory('context', function($rootScope, $http, $q) {
		var items = [];
		var context = {};

		context.addItem = function(item) {
			items.push(item);
		};
		context.clear = function() {
			items = [];
		};
		context.removeItem = function(item) {
			var index = items.indexOf(item);
			items.splice(index, 1);
		};
		context.items = function() {
			return items;
		};

		return context;
	}).
	factory('socket', function ($rootScope) {
        var socket = new WebSocket('ws://'+window.location.host+'/ws/');
        var callbacks = {};
        socket.onmessage = function (e) {
            var data = JSON.parse(e.data);
            var currentCallbacks = callbacks[data['eventName']];
            for (var i = 0; i < currentCallbacks.length; i++) {
                var callback = currentCallbacks[i];
                var args = arguments;
                $rootScope.$apply(function () {
                    callback.apply(socket, args);
                });
            }
        };
		return {
			on: function (eventName, callback) {
                if (!callbacks[eventName]) {
                    callbacks[eventName] = [];
                }
                callbacks[eventName].push(callback);
			},
			emit: function (eventName, data, callback) {
                var data = {'eventName': eventName, 'eventData': data};
                data = JSON.stringify(data);
				socket.send(data);
			}
		};
	}).
  config(function($routeProvider, $locationProvider) {
	//$locationProvider.html5Mode(true);
	$routeProvider.
		  when('/', {templateUrl: '/partials/welcome.html', controller: WelcomeCtrl}).
		  when('/about', {templateUrl: '/partials/about.html', controller: AboutCtrl}).
	      when('/google/login', {templateUrl: '/partials/google_login.html', controller: GoogleLoginCtrl}).
		  when('/spotify/login', {templateUrl: '/partials/spotify_login.html', controller: SpotifyLoginCtrl}).
		  when('/spotify/playlists/select', {templateUrl: '/partials/playlists.html', controller: SelectSpotifyCtrl}).
		  when('/transfer/process_fancy', {templateUrl: '/partials/fancy_process.html', controller: FancyProcessTransferCtrl}).
		  when('/transfer/process', {templateUrl: '/partials/process.html', controller: ProcessTransferCtrl}).
	      otherwise({redirectTo: '/'});
  }).
	directive('scrollGlue', function() {
		return {
			priority: 1,
			require: ['?ngModel'],
			restrict: 'A',
			link: function(scope, $el, attrs, ctrls) {
				var el = $el[0];
				var lastScroll = -1;

				function scrollToBottom() {
					if(el.scrollTop < el.scrollHeight && el.scrollHeight > lastScroll) {
						lastScroll = el.scrollHeight;
						var targetScroll = el.scrollHeight;
						$(el).animate( {
							scrollTop: targetScroll
						}, 500);
					}
				}

				scope.$watch(function() {
					scrollToBottom();
				});
			}
		}});
