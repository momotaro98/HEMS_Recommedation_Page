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
