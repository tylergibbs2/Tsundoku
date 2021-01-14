interface NyaaIndividualResult {
    show_id?: number;
    title: string;
    post_link: string;
    torrent_link: string;
    size: string;
    published: string;
    seeders: number;
    leechers: number;
}

interface NyaaSearchResult {
    status: number;
    result: NyaaIndividualResult[];
}

var modalsCanBeClosed: boolean = true;


function closeSearchModal() {
    if (modalsCanBeClosed) {
        $(".modal").removeClass("is-active");
        $(document.documentElement).removeClass("is-clipped");
    }
}

function openResultUpsertModal(torrent_link: string) {
    $(".modal").addClass("is-active");
    $(document.documentElement).addClass("is-clipped");
}

function populateSearchResultTable(data: NyaaSearchResult) {
    if (data.result.length === 0) {
        $("#space-holder").removeClass("is-hidden");
        $("#search-result-table").addClass("is-hidden");
        return;
    } else {
        $("#space-holder").addClass("is-hidden");
        $("#search-result-table").removeClass("is-hidden");
    }

    $("#search-result-table table tbody").empty();

    for (const row of data.result) {
        $("#search-result-table table tbody").append(
            `
            <tr onclick="openResultUpsertModal(${row.torrent_link});">
                <td style="width: 60%;">${row.title}</td>
                <td>${row.size}</td>
                <td>${row.published}</td>
                <td class="has-text-success">${row.seeders}</td>
                <td class="has-text-danger">${row.leechers}</td>
                <td><a href="${row.post_link}">Link</a></td>
            </tr>
            `
        );
    }
}

function watchSearchBox() {
    let timer: number;
    let waitInterval: number = 2250;

    $("#search-box-div input").on("keyup", function() {
        clearTimeout(timer);
        timer = setTimeout(searchForResults, waitInterval);
    });

    $("#search-box-div input").on("keydown", function() {
        clearTimeout(timer);
    })
}

function searchForResults() {
    let searchQuery: string = $("#search-box-div input").val() as string;

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
        success: function(data: NyaaSearchResult) {
            populateSearchResultTable(data);
        },
        complete: function() {
            $("#search-box-div").removeClass("is-loading");
        }
    });
}

$(function() {
    watchSearchBox();
});