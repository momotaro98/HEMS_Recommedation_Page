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
