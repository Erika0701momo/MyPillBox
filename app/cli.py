import os
import click
from flask import Blueprint

bp = Blueprint("cli", __name__, cli_group=None)


@bp.cli.group()
def translate():
    """翻訳とローカライゼーションのコマンドたち"""
    pass


@translate.command()
def update():
    """全ての言語をアップデート"""
    if os.system("pybabel extract -F babel.cfg -k _l -o messages.pot ."):
        raise RuntimeError("extractコマンドは失敗しました")
    if os.system("pybabel update -i messages.pot -d app/translations"):
        raise RuntimeError("updateコマンドは失敗しました")
    os.remove("messages.pot")


@translate.command()
def compile():
    """全ての言語をコンパイル"""
    if os.system("pybabel compile -d app/translations"):
        raise RuntimeError("compileコマンドは失敗しました")


@translate.command()
@click.argument("lang")
def init(lang):
    """新しい言語をイニシャライズ"""
    if os.system("pybabel extract -F babel.cfg -k _l -o messages.pot ."):
        raise RuntimeError("extractコマンドは失敗しました")
    if os.system("pybabel init -i messages.pot -d app/translations -l " + lang):
        raise RuntimeError("initコマンドは失敗しました")
    os.remove("messages.pot")
