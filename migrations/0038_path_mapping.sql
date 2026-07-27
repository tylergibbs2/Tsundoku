-- remote_prefix_key is the case-folded form of remote_prefix for
-- Windows-flavoured paths, which compare case-insensitively. Uniqueness is
-- enforced on the key rather than on remote_prefix so that 'D:\Torrents' and
-- 'd:\torrents' cannot both be stored while naming the same directory.
CREATE TABLE path_mapping (
    id INTEGER PRIMARY KEY,
    remote_prefix TEXT NOT NULL,
    remote_prefix_key TEXT NOT NULL UNIQUE,
    local_prefix TEXT NOT NULL
);
