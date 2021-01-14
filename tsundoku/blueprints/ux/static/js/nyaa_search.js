var modalsCanBeClosed = true;
function closeSearchModal() {
    if (modalsCanBeClosed) {
        $(".modal").removeClass("is-active");
        $(document.documentElement).removeClass("is-clipped");
    }
}
function populateSearchResultTable(data) {
    if (data.result.length === 0) {
        $("#space-holder").removeClass("is-hidden");
        $("#search-result-table").addClass("is-hidden");
        return;
    }
    else {
        $("#space-holder").addClass("is-hidden");
        $("#search-result-table").removeClass("is-hidden");
    }
    $("#search-result-table table tbody").empty();
    for (var _i = 0, _a = data.result; _i < _a.length; _i++) {
        var row = _a[_i];
        $("#search-result-table table tbody").append("\n            <tr class=\"is-clickable\">\n                <td style=\"width: 60%;\">" + row.title + "</td>\n                <td>" + row.size + "</td>\n                <td>" + row.published + "</td>\n                <td class=\"has-text-success\">" + row.seeders + "</td>\n                <td class=\"has-text-danger\">" + row.leechers + "</td>\n                <td><a href=\"" + row.post_link + "\">Link</a></td>\n            </tr>\n            ");
    }
}
function watchSearchBox() {
    var timer;
    var waitInterval = 2250;
    $("#search-box-div input").on("keyup", function () {
        clearTimeout(timer);
        timer = setTimeout(searchForResults, waitInterval);
    });
    $("#search-box-div input").on("keydown", function () {
        clearTimeout(timer);
    });
}
function searchForResults() {
    var searchQuery = $("#search-box-div input").val();
    if (!searchQuery) {
        $("#space-holder").removeClass("is-hidden");
        $("#search-result-table").addClass("is-hidden");
        return;
    }
    $("#search-box-div").addClass("is-loading");
    $.ajax({
        url: "/api/v1/nyaa",
        type: "GET",
        data: {
            query: searchQuery
        },
        success: function (data) {
            populateSearchResultTable(data);
        },
        complete: function () {
            $("#search-box-div").removeClass("is-loading");
        }
    });
}
$(function () {
    watchSearchBox();
});
