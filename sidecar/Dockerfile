FROM php:8.2-apache

# Install Git and dependencies
RUN apt-get update && apt-get install -y git libxml2-dev \
    && docker-php-ext-install dom xml mbstring \
    && a2enmod rewrite \
    && echo "post_max_size=10M\nupload_max_filesize=10M\nmemory_limit=256M" > /usr/local/etc/php/conf.d/limits.ini \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /var/www/html

# Create the dummy library structure
RUN mkdir -p dummy_lib/lib && \
    touch dummy_lib/lib/backend.php && \
    touch dummy_lib/lib/fuckhtml.php

# Copy source code
COPY src/ /var/www/html/
COPY entrypoint.sh /usr/local/bin/

RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["entrypoint.sh"]
CMD ["apache2-foreground"]