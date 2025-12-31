FROM php:8.2-apache

# 1. Install dependencies
# Added 'wget' and 'ca-certificates' which are required to download curl-impersonate
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
    && a2enmod rewrite \
    && rm -rf /var/lib/apt/lists/*

# 2. Install curl-impersonate (Chrome & Firefox versions)
# This installs the special curl binaries to /usr/local/bin
RUN wget -O- https://github.com/lwthiker/curl-impersonate/releases/download/v0.6.1/curl-impersonate-v0.6.1.x86_64-linux-gnu.tar.gz \
    | tar -xz -C /usr/local/bin

WORKDIR /var/www/html

# 3. Clone 4get-repo during build to make startup instant
RUN git clone --depth 1 https://git.lolcat.ca/lolcat/4get.git /var/www/html/4get-repo \
    && chown -R www-data:www-data /var/www/html/4get-repo

# 4. Create dummy lib to prevent 4get from loading real backend/fuckhtml
RUN mkdir -p dummy_lib/lib && \
    touch dummy_lib/lib/backend.php && \
    touch dummy_lib/lib/fuckhtml.php

COPY src/ /var/www/html/
COPY entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh \
    && chown www-data:www-data /usr/local/bin/entrypoint.sh

# Ensure web server has access to all files
RUN chown -R www-data:www-data /var/www/html

# Use tini to manage the process headers
ENTRYPOINT ["/usr/bin/tini", "--", "entrypoint.sh"]
CMD ["apache2-foreground"]