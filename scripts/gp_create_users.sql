create user bench with password 'password';
create role users;
grant all privileges on database dbbench to bench;
grant pg_read_server_files to bench;
grant users to bench;
