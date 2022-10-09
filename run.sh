docker build -t cms .
docker run --rm -d -e CMS_SERVER_TOKEN=foobar -e CMS_PORT=8001 -p 8001:8001 --name cms --network badideas cms
docker run --rm --network badideas \
   -v $(pwd)/nginx/default.conf:/etc/nginx/conf.d/default.conf \
   -v $(pwd)/www:/srv/www \
   -p 8000:80 \
   --name nginx \
   nginx
