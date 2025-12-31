FROM php:8.2-apache

# 1. Install dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    ca-certificates \
    libxml2-dev \
    libonig-dev \
    libcurl4-openssl-dev \
    tini \
    && docker-php-ext-install dom xml mbstring curl \
    && pecl install apcu \
    && docker-php-ext-enable apcu \
    # Enable APCu for CLI scripts (critical for the backend logic)
    && echo "apc.enable_cli=1" >> /usr/local/etc/php/conf.d/docker-php-ext-apcu.ini \
    && a2enmod rewrite \
    && rm -rf /var/lib/apt/lists/*

# 2. Install curl-impersonate
RUN wget -O- https://github.com/lwthiker/curl-impersonate/releases/download/v0.6.1/curl-impersonate-v0.6.1.x86_64-linux-gnu.tar.gz \
    | tar -xz -C /usr/local/bin

# 3. Symlink to the name 4get looks for internally
# This allows 4get to find the stealth binary naturally
RUN ln -s /usr/local/bin/curl-impersonate-chrome /usr/local/bin/curl_chrome116

WORKDIR /var/www/html

# 4. Clone 4get-repo
RUN git clone --depth 1 https://git.lolcat.ca/lolcat/4get.git /var/www/html/4get-repo \
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