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
    },FillStatsTable(data));
}

function showDatabaseInfo(){
	var $BATTLES_THRESHOLD = 1000
    $.getJSON($SCRIPT_ROOT + '/databaseinfo',{
        battles:$BATTLES_THRESHOLD
    },function(data){
        $('#StatsOfTheWeekOutput').text("Active players number: " + data.active_player_number + " (plays at least " + $BATTLES_THRESHOLD + " battles)");
    });
}

function fillStatsTable(data){
    document.getElementById("table_stats_of_the_week").style.display="table";
}