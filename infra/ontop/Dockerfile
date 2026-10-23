FROM ontop/ontop:5.4.0

# The base image does not include JDBC drivers.
ADD --chmod=644 https://repo1.maven.org/maven2/org/postgresql/postgresql/42.7.4/postgresql-42.7.4.jar /opt/ontop/jdbc/postgresql-42.7.4.jar

# ADD also applies its mode to newly created parent directories on a clean build.
USER root
RUN chmod 755 /opt/ontop/jdbc
USER ontop
