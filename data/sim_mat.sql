CREATE TABLE `drama` (
    `id` INT NOT NULL,
    `title` VARCHAR(255) NOT NULL,
    `pic_url` VARCHAR(255) NOT NULL,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE cos_sim (
    `id` INT NOT NULL,
    `rank` INT NOT NULL,
    `sim_val` DOUBLE,
    `rank_id` INT NOT NULL,
    CONSTRAINT `fk_cos_sim_id` FOREIGN KEY (`id`) REFERENCES `drama` (`id`)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_cos_sim_rank_id` FOREIGN KEY (`rank_id`) REFERENCES `drama` (`id`)
        ON DELETE CASCADE ON UPDATE CASCADE,
    PRIMARY KEY (`id`, `rank`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `app_user` (
    `google_sub` VARCHAR(255) NOT NULL,
    `avatar_url` VARCHAR(2048) NULL,
    `wl_sz` INT NOT NULL DEFAULT 0,
    PRIMARY KEY (`google_sub`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `watch_list` (
    `google_sub` VARCHAR(255) NOT NULL,
    `id` INT NOT NULL,

    PRIMARY KEY (`google_sub`, `id`),
    CONSTRAINT `fk_watch_list_user` FOREIGN KEY (`google_sub`) REFERENCES `app_user` (`google_sub`)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_watch_list_id` FOREIGN KEY (`id`) REFERENCES `drama` (`id`)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `rec_list` (
    `rank` INT NOT NULL,
    `google_sub` VARCHAR(255) NOT NULL,
    `sim` DOUBLE NOT NULL,
    `id` INT NOT NULL,
    `tag` INT NOT NULL,
    PRIMARY KEY (`id`),
    CONSTRAINT `fk_rec_list_user` FOREIGN KEY (`google_sub`) REFERENCES `app_user` (`google_sub`)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_rec_list_id` FOREIGN KEY (`id`) REFERENCES `drama` (`id`)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_rec_list_tag` FOREIGN KEY (`tag`) REFERENCES `drama` (`id`)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_rec on rec_list (`google_sub`, `rank`);
CREATE INDEX upd_rec on rec_list (`google_sub`);
CREATE INDEX tag_rec on rec_list (`google_sub`,`tag`);
CREATE INDEX idx_watch on watch_list (`google_sub`);
CREATE INDEX upd_watch on watch_list (`google_sub`, `id`);
CREATE INDEX idx_cos on cos_sim (`id`, `rank`);
CREATE INDEX idx_drama on drama (`id`);
CREATE INDEX search_drama on drama (`title`);
CREATE INDEX idx_user on app_user (`google_sub`);