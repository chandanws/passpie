# -*- coding: utf-8 -*-
import re

import pytest

from passpie.cli import (
    KEY_INPUT,
    DEVNULL,
    make_key_input,
    export_keys,
    import_keys,
    list_keys,
    create_keys,
    Response,
    encrypt,
    decrypt,
    get_default_recipient,
)


def test_crypt_make_key_input_create_key_with_expect_values(mocker):
    passphrase = 'passphrase'
    key_length = 2064
    defaults = {}
    defaults["name"] = "Passpie"
    defaults["email"] = "passpie@localhost"
    defaults["comment"] = "Generated by Passpie"
    defaults["expire_date"] = 0
    key_input = KEY_INPUT.format(
        key_length,
        defaults["comment"],
        passphrase,
        defaults["name"],
        defaults["email"],
        defaults["expire_date"],
    )
    assert key_input == make_key_input(
        key_length=key_length, passphrase=passphrase)


def test_crypt_make_key_input_handles_unicode_encode_error(mocker):
    passphrase = u"L'éphémère"
    key_length = 2064
    key_input = make_key_input(key_length=key_length, passphrase=passphrase)

    assert key_input is not None


def test_crypt_export_keys_calls_gpg_command_on_export_keys(mocker, mock_run):
    mock_run.return_value.std_out = 'exported keys'
    mocker.patch('passpie.cli.which', return_value='gpg')
    homedir = 'mock_homedir'
    fingerprint = 'mock_fingerprint'

    secret = False
    command = [
        'gpg',
        '--no-tty',
        '--batch',
        '--homedir', homedir,
        '--export-secret-keys' if secret else '--export',
        '--armor',
        '-o', '-',
        fingerprint,
    ]
    exported_keys = export_keys(homedir, fingerprint)

    assert mock_run.called is True
    assert exported_keys == "exported keys"
    mock_run.assert_called_once_with(command)


def test_encrypt_calls_gpg_encrypt_command_with_recipient(mocker, mock_run):
    mocker.patch('passpie.cli.which', return_value='gpg')
    recipient = 'passpie@local'
    password = 's3cr3t'
    mock_run.return_value.stdout = '--GPG ENCRYPTED--'
    homedir = 'homedir'
    command = [
        'gpg',
        '--batch',
        '--no-tty',
        '--always-trust',
        '--armor',
        '--recipient', recipient,
        '--homedir', homedir,
        '--encrypt'
    ]
    result = encrypt(password, recipient, homedir)

    assert result is not None
    assert mock_run.called
    mock_run.assert_called_once_with(command, data=password)


def test_decrypt_calls_gpg_encrypt_expected_command(mocker, mock_run):
    mocker.patch('passpie.cli.which', return_value='gpg')
    recipient = 'passpie@local'
    passphrase = 'passphrase'
    homedir = 'homedir'
    data = '--GPG ENCRYPTED--'
    mock_run.return_value.stdout = 's3cr3t'
    command = [
        'gpg',
        '--batch',
        '--no-tty',
        '--always-trust',
        '--recipient', recipient,
        '--homedir', homedir,
        '--passphrase', passphrase,
        '--emit-version',
        '-o', '-',
        '-d', '-',
    ]
    result = decrypt(data, recipient, homedir=homedir, passphrase=passphrase)

    assert result is not None
    assert mock_run.called
    mock_run.assert_called_once_with(command, data=data)


def test_default_recipient_returns_first_matched_fingerprint(mocker, mock_run):
    mocker.patch('passpie.cli.list_keys', return_value=["123", "456"])
    recipient = get_default_recipient('homedir')
    assert recipient == '123'


def test_list_keys_calls_expected_command_when_secret_is_true(mocker, mock_run):
    mocker.patch('passpie.cli.mkdtemp')
    mocker.patch('passpie.cli.import_keys')
    mocker.patch('passpie.cli.which', return_value='gpg')
    recipient = list_keys('homedir')

    command = [
        'gpg',
        '--no-tty',
        '--batch',
        '--fixed-list-mode',
        '--with-colons',
        '--homedir', 'homedir',
        "--list-keys",
        '--fingerprint',
    ]

    assert mock_run.called is True
    mock_run.assert_called_once_with(command)