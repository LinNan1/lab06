FROM python:3.7
ADD example.py /
ADD requirements.txt /
RUN pip3 install --trusted-host pypi.python.org -r requirements.txt
EXPOSE 5000
ENTRYPOINT ["./example.py"]

