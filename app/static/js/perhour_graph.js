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
