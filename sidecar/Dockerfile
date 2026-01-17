FROM php:8.2-apache

# 1. Install dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    ca-certificates \
    libxml2-dev \
    libonig-dev \
    libcurl4-openssl-dev \
    tini \
    && docker-php-ext-install dom xml mbstring curl \
    && pecl install apcu \
    && docker-php-ext-enable apcu \
    # Enable APCu for CLI and increase memory for token storage
    && echo "apc.enable_cli=1" >> /usr/local/etc/php/conf.d/docker-php-ext-apcu.ini \
    && echo "apc.shm_size=128M" >> /usr/local/etc/php/conf.d/docker-php-ext-apcu.ini \
    # Enable OPcache for 2-3x sidecar speedup (caches compiled PHP bytecode)
    && docker-php-ext-enable opcache \
    && echo "opcache.memory_consumption=128" >> /usr/local/etc/php/conf.d/docker-php-ext-opcache.ini \
    && echo "opcache.max_accelerated_files=10000" >> /usr/local/etc/php/conf.d/docker-php-ext-opcache.ini \
    && echo "opcache.validate_timestamps=0" >> /usr/local/etc/php/conf.d/docker-php-ext-opcache.ini \
    && a2enmod rewrite \
    && rm -rf /var/lib/apt/lists/*

# 2. Install curl-impersonate (extract to /usr/local so lib/ and bin/ are populated)
RUN wget -O- https://github.com/lwthiker/curl-impersonate/releases/download/v0.6.1/libcurl-impersonate-v0.6.1.x86_64-linux-gnu.tar.gz \
    | tar -xz -C /usr/local/lib

# 3. Set environment variables for PHP to use curl-impersonate (Firefox to match 4get's UA)
ENV LD_PRELOAD=/usr/local/lib/libcurl-impersonate-ff.so
ENV CURL_IMPERSONATE=ff117

WORKDIR /var/www/html

# 4. Clone 4get-repo (SSL verify disabled - git.lolcat.ca has untrusted cert)
RUN GIT_SSL_NO_VERIFY=1 git clone --depth 1 https://git.lolcat.ca/lolcat/4get.git /var/www/html/4get-repo \
    && chown -R www-data:www-data /var/www/html/4get-repo

# 5. Create dummy lib structure
RUN mkdir -p dummy_lib/lib && \
    touch dummy_lib/lib/backend.php && \
    touch dummy_lib/lib/fuckhtml.php

COPY src/ /var/www/html/
COPY entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh \
    && chown www-data:www-data /usr/local/bin/entrypoint.sh

RUN chown -R www-data:www-data /var/www/html

ENTRYPOINT ["/usr/bin/tini", "--", "entrypoint.sh"]
CMD ["apache2-foreground"]