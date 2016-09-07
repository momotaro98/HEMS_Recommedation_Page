(function(){
	// 設定温度
	var settemp_data_out = {
	  labels: settemp_lables,
	  datasets: [
		{
		  label: '設定温度使用割合[%]',
		  hoverBackgroundColor: "rgba(255,99,132,0.3)",
		  data: settemp_data,
		}
	  ]
	};

	//「オプション設定」
	var options = {
	  title: {
		display: true,
		text: 'エアコン設定温度の使用割合'
	  }
	};

	var canvas = document.getElementById('settemp');
	var chart = new Chart(canvas, {

	  type: 'bar',  //グラフの種類
	  data: settemp_data_out,  //表示するデータ
	  options: options  //オプション設定

	});
}());


(function(){
	// 運転時間合計
	var totaltime_data_out = {
	  labels: totaltime_lables,
	  datasets: [
		{
		  label: '運転時間[時間]',
		  hoverBackgroundColor: "rgba(255,99,132,0.3)",
		  data: totaltime_data,
		}
	  ]
	};

	//「オプション設定」
	var options = {
	  title: {
		display: true,
		text: '1日当たりのエアコン作動時間'
	  }
	};

	var canvas = document.getElementById('totaltime');
	var chart = new Chart(canvas, {

	  type: 'bar',  //グラフの種類
	  data: totaltime_data_out,  //表示するデータ
	  options: options  //オプション設定

	});
}());


(function(){
	// 単位時間当たりの使用率グラフ
	var perhour_data_out = {
	  labels: perhour_lables,
	  datasets: [
		{
		  label: 'エアコン使用率[%]',
		  hoverBackgroundColor: "rgba(255,99,132,0.3)",
		  data: perhour_data,
		}
	  ]
	};

	//「オプション設定」
	var options = {
	  title: {
		display: true,
		text: '1時間当たりのエアコン平均使用率'
	  }
	};

	var canvas = document.getElementById('perhour');
	var chart = new Chart(canvas, {

	  type: 'line',  //グラフの種類
	  data: perhour_data_out,  //表示するデータ
	  options: options  //オプション設定

	});
}());
