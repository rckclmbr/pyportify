function MainCtrl($scope, $route, $routeParams, $location, context) {
	$scope.context = context.items();
	$scope.app_name = "Pyportify";
}

function WelcomeCtrl($scope, $rootScope, $route, $routeParams, $location) {
	$rootScope.step = 0;
	$rootScope.link = '<a href="#/about" class="btn btn-danger">About Pyportify</a>';
}

function AboutCtrl($scope, $rootScope, $route, $routeParams, $location) {
	$rootScope.link = '<a href="#/" class="btn btn-danger">&laquo; Back</a>';
}

function ProcessTransferCtrl($scope, $rootScope, $filter, $http, $route, $routeParams, $location, socket, context, portifyService, $timeout, $anchorScroll) {
	$rootScope.step = 4;
	$rootScope.link = '';
	$scope.playlists = context.items();
	$scope.alldone = false;
	$scope.processing = false;

	$scope.notfound = [];
	$scope.shownotfound = false;

	$scope.currentPlaylist = {
		name: "",
		processed: 0,
		found: 0,
		notfound: 0,
		karaoke: 0,
		count: 0,
		progress: 0,
	};

	$timeout(function() {
		portifyService.startTransfer($scope.playlists);
	}, 600);

	$scope.hideMissing = function() {
		$scope.shownotfound = false;
	};

	$scope.showMissing = function() {
		$scope.shownotfound = true;
	};

	socket.on('portify', function (data) {
        data = JSON.parse(data.data)['eventData']
		if(data.type == "playlist_started") {
			$scope.cover = null;
			$scope.playlist = data.data.playlist.name;
			$scope.status = "Transfering..."+$scope.playlist;
			$scope.tracks = [];
			$scope.currentPlaylist = {
				name: data.data.playlist.name,
				processed: 0,
				found: 0,
				notfound: 0,
				karaoke: 0,
				count: 0,
				progress: 0
			};
			$scope.processing = true;
		} else if(data.type == "all_done") {
			$scope.alldone = true;
		} else if(data.type == "playlist_done") {
			$scope.processing = false;
		} else if(data.type = "playlist_length") {
			$scope.currentPlaylist.count = data.data.length;
		}
	});

	socket.on('gmusic', function (data) {
        data = JSON.parse(data.data)['eventData']
		if(data.type == "added") {
			$scope.currentPlaylist.processed++;
			$scope.currentPlaylist.found++;
		} else if(data.type == "not_added") {
			$scope.notfound.push({"name": data.data.spotify_track_name});
			$scope.currentPlaylist.processed++;
			$scope.currentPlaylist.notfound++;
			if(data.data.karaoke) {
				$scope.currentPlaylist.karaoke++;
			}
		}
		if($scope.currentPlaylist.count == 0)
			$scope.currentPlaylist.progress = "0%";
		else
			$scope.currentPlaylist.progress = (($scope.currentPlaylist.processed / $scope.currentPlaylist.count)*100) +"%";
	});
}

function FancyProcessTransferCtrl($scope, $rootScope, $filter, $http, $route, $routeParams, $location, socket, context, portifyService, $timeout, $anchorScroll) {
	$rootScope.step = 4;
	$rootScope.link = '';
	$scope.playlists = context.items();
	$scope.tracks = [];
	$scope.playlistsDone = 0;
	$scope.alldone = false;
	$scope.ttracks =  [];
	portifyService.startTransfer($scope.playlists);


	function findIndexByKeyValue(obj, key, value) {
		for (var i = 0; i < obj.length; i++) {
			if (obj[i][key] == value) {
				return i;
			}
		}
		return null;
	}

	socket.on('portify', function (data) {
        data = JSON.parse(data.data)['eventData']
		if(data.type == "playlist_started") {
			$scope.playlist = data.data.playlist.name;
			$scope.status = "Transfering..."+$scope.playlist;
			$scope.tracks = [];
		} else if(data.type == "all_done") {
			$scope.alldone = true;
		}
	});

	socket.on('gmusic', function (data) {
        data = JSON.parse(data.data)['eventData']
		var myidx = findIndexByKeyValue($scope.tracks, "id", data.data.spotify_track_uri );
		if(data.type == "found_possible_matches") {

			if(data.data.found) {
				//$scope.tracks[data.data.spotify_track_uri].class.push('color');
				$scope.tracks[myidx].class.push('color');
			} else {
				//$scope.tracks[data.data.spotify_track_uri].nok = true;
				$scope.tracks[myidx].nok = true;
			}
		} else if(data.type == "added") {
			$scope.tracks[myidx].ok = true;
		}
	});

	socket.on('spotify', function (data) {
		if(data.type == "track") {
			var image = new Image();
			image.src = data.data.cover;
			image.onload = function(){
				$scope.tracks.push({ id: data.data.spotify_track_uri, src: data.data.cover, class: ['album', '']});
				$scope.ttracks = $filter('limitTo')($scope.tracks,-60);
			}
		}
	});
}

function GoogleLoginCtrl($scope, $rootScope, $http, $location, socket) {
	$rootScope.step = 1;
	$rootScope.link = '';
	$scope.googleLogin = function() {
		$http({
			url: "/google/login",
			dataType: "json",
			method: "POST",
			data: $scope.loginData,
			headers: {
				"Content-Type": "application/json; charset=utf-8"
			}
		}).success(function(response){
			if(response.status == 200) {
				$location.path( "/spotify/login" );
			} else {
				alert("Login failed.");
			}
		}).error(function(error){
			$scope.error = error;
		});
	};
	socket.on('test', function (data) {
        console.log(data);
	});
}

function SpotifyLoginCtrl($scope, $rootScope, $http, $location) {
	$rootScope.step = 2;
	$rootScope.link = '';
	$scope.spotifyLogin = function() {
		$http({
			url: "/spotify/login",
			dataType: "json",
			method: "POST",
			data: $scope.loginData,
			headers: {
				"Content-Type": "application/json; charset=utf-8"
			}
		}).success(function(response){
			if(response.status == 200) {
				$location.path( "/spotify/playlists/select" );
			} else {
				alert("Login failed.");
			}
		}).error(function(error){
			$scope.error = error;
		});
	};
}

function SelectSpotifyCtrl($scope, $rootScope, $http, $location, portifyService, context) {
	$scope.playlists = portifyService.getSpotifyPlaylists();
	$rootScope.step = 3;
	$rootScope.link = '';
	$scope.selectAll = function ($event){
		var checkbox = $event.target;
		for ( var i = 0; i < $scope.playlists.$$v.length; i++) {
			$scope.playlists.$$v[i].transfer = checkbox.checked;
		}
	};

	$scope.startTransfer = function() {
		context.clear();
		for ( var i = 0; i < $scope.playlists.$$v.length; i++) {
			if($scope.playlists.$$v[i].transfer) {
				context.addItem($scope.playlists.$$v[i]);
			}
		}

		if(context.items().length == 0)
			alert("Please select at least one playlist");
		else
			$location.path( "/transfer/process" );
	}
}
