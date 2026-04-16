@echo off
setlocal
set JAVA_CMD=%JAVA_HOME%\bin\java.exe
if not exist "%JAVA_CMD%" set JAVA_CMD=java

set CLASSPATH=%~dp0gradle\wrapper\gradle-wrapper.jar
"%JAVA_CMD%" -cp "%CLASSPATH%" org.gradle.wrapper.GradleWrapperMain %*
