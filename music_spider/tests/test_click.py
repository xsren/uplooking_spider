"""
参考：http://python.jobbole.com/87111/
"""
# coding:utf8
import click


@click.command()
@click.option('--param', default=1, help='description')
def run(param):
    print(param)


if __name__ == '__main__':
    run()