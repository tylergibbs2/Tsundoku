INSERT INTO library (
    id,
    folder,
    is_default
)
VALUES
    (1, "anime1", 1),
    (2, "anime2", 0);


INSERT INTO shows (
    id,
    library_id,
    title,
    title_local,
    desired_format,
    season,
    episode_offset,
    watch,
    preferred_resolution,
    preferred_release_group
)
VALUES
    (1, 1, "Chainsaw Man", NULL, "{n} - {s00e00}", 1, 0, 1, NULL, NULL),
    (2, 2, "Buddy Daddies", NULL, "{n} - {s00e00}", 2, 3, 1, NULL, NULL),
    (3, 1, "NieR Automata Ver1.1a", "NIER LOCAL", "{n} - {s00e00}", 1, 0, 1, "1080p", NULL);