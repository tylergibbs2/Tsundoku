INSERT INTO shows (
    id,
    title,
    desired_format,
    desired_folder,
    season,
    episode_offset,
    watch,
    post_process,
    preferred_resolution,
    preferred_release_group
)
VALUES
    (1, "Chainsaw Man", "{n} - {s00e00}", "/target/{n}/Season {s00}", 1, 0, 1, 1, NULL, NULL),
    (2, "Buddy Daddies", "{n} - {s00e00}", "/target/{n}/Season {s00}", 1, 0, 1, 1, NULL, NULL),
    (3, "NieR Automata Ver1.1a", "{n} - {s00e00}", "/target/{n}/Season {s00}", 1, 0, 1, 0, "1080p", NULL);