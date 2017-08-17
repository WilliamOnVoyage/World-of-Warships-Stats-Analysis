// $('#ovallstats').addEventListener('click',OverallStats());
// $('#statsoftheweek').addEventListener('click',StatsOfTheWeek());
// $('#statsofthemonth').addEventListener('click',StatsOfTheMonth());

function statsOfTheWeek(){
	showDatabaseInfo();
}

function statsOfTheMonth(){
	showDatabaseInfo();
}

function overallStats(){
	showDatabaseInfo();
	var $BATTLES_THRESHOLD = 1000
	$.getJSON($SCRIPT_ROOT + '/overallstats',{
		battles:$BATTLES_THRESHOLD
	},function(data){
		buildOverallStatsTable(data);
	});
}

function showDatabaseInfo(){
	var $BATTLES_THRESHOLD = 1000
	$.getJSON($SCRIPT_ROOT + '/databaseinfo',{
		battles:$BATTLES_THRESHOLD
	},function(data){
		$('#StatsOfTheWeekOutput').text("Active players number: " + data.active_player_number + " (plays at least " + $BATTLES_THRESHOLD + " battles)");
	});
}

function buildOverallStatsTable(data){
	var $TABLE_NAME = "#table_overall_stats"
	// deleteAllTableRows($TABLE_NAME);

	data_list = data.player_list
	var columnSet = ['Player','Battles','Wins','Losses'];
	var headerTr$ = $('<tr/>');
	for(var key in columnSet){
		headerTr$.append($('<th/>').html(columnSet[key]));
	}
	$($TABLE_NAME).append(headerTr$);

	for(var item in data_list){
		var player = JSON.parse(data_list[item])[0];
		var tr = $('<tr/>');
		tr.append('<td>'+player['nickname']+'</td>');
		tr.append('<td>'+player['statistics.pvp.battles']+'</td>');
		tr.append('<td>'+player['statistics.pvp.wins']+'</td>');
		tr.append('<td>'+player['statistics.pvp.losses']+'</td>');
		$($TABLE_NAME).append(tr);
	}
	document.getElementById($TABLE_NAME).style.visibility="visible";
}

function deleteAllTableRows(tablename){
	var tb = document.getElementById(tablename);
	var rowNum=tb.rows.length;
	for (i=0;i<rowNum;i++)
	{
		tb.deleteRow(i);
		rowNum=rowNum-1;
		i--;
	}
}
