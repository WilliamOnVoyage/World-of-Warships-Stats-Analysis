function StatsOfTheWeek(){
		var $BATTLES_THRESHOLD = 100
    $.getJSON($SCRIPT_ROOT + '/databaseinfo',{
        battles:$BATTLES_THRESHOLD
    },function(data){
        $('#StatsOfTheWeekOutput').text("Active players number: " + data.active_player_number + " (plays at least " + $BATTLES_THRESHOLD + " battles)");
    });
}

function StatsOfTheMonth(){
    	var $BATTLES_THRESHOLD = 100
    $.getJSON($SCRIPT_ROOT + '/databaseinfo',{
        battles:$BATTLES_THRESHOLD
    },function(data){
        $('#StatsOfTheWeekOutput').text("Active players number: " + data.active_player_number + " (plays at least " + $BATTLES_THRESHOLD + " battles)");
    });
}

function OverallStats(){
    	var $BATTLES_THRESHOLD = 100
    $.getJSON($SCRIPT_ROOT + '/databaseinfo',{
        battles:$BATTLES_THRESHOLD
    },function(data){
        $('#StatsOfTheWeekOutput').text("Active players number: " + data.active_player_number + " (plays at least " + $BATTLES_THRESHOLD + " battles)");
    });
    // var $BATTLES_THRESHOLD = 1000
    // $.getJSON($SCRIPT_ROOT + '/overallstats',{
    //     battles:$BATTLES_THRESHOLD
    // },FillStatsTable(data));
}

function ShowDatabaseInfo(){
	var $BATTLES_THRESHOLD = 100
    $.getJSON($SCRIPT_ROOT + '/databaseinfo',{
        battles:$BATTLES_THRESHOLD
    },function(data){
        $('#StatsOfTheWeekOutput').text("Active players number: " + data.active_player_number + " (plays at least " + $BATTLES_THRESHOLD + " battles)");
    });
}

function FillStatsTable(data){
    document.getElementById("table_stats_of_the_week").style.display="table";
}