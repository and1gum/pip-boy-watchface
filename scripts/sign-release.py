#!/usr/bin/env python3
"""Explicit permanent signing-key setup and release signing; secrets never enter Git."""
import argparse
import hashlib
import os
from pathlib import Path
import secrets
import shutil
import subprocess


def run(*args, **kwargs):
    return subprocess.run(list(map(str, args)), check=True, **kwargs)


def init(directory, backup, old_key, references):
    directory, backup, old_key = map(lambda p: Path(p).expanduser().resolve(), (directory, backup, old_key))
    repo = Path(__file__).resolve().parents[1]
    for path in (directory, backup):
        if path.is_relative_to(repo):
            raise ValueError('Signing secrets and their backup must be outside the repository')
    if directory == backup or directory.is_relative_to(backup) or backup.is_relative_to(directory):
        raise ValueError('Use independent signing and backup directories')
    if directory.exists() or backup.exists():
        raise ValueError('Refusing to overwrite existing signing or backup directory')
    if not old_key.is_file():
        raise ValueError('Original debug keystore is required for state-preserving migration')
    tool = Path(os.environ['ANDROID_HOME']) / 'build-tools/35.0.0/apksigner'
    env = dict(os.environ, PIPBOY_OLD_PASS=os.environ.get('PIPBOY_DEBUG_PASSWORD', 'android'))
    certificate = run('keytool', '-exportcert', '-keystore', old_key, '-alias', 'androiddebugkey',
                      '-storepass:env', 'PIPBOY_OLD_PASS', env=env, capture_output=True).stdout
    fingerprint = hashlib.sha256(certificate).hexdigest()
    for apk in references:
        output = run(tool, 'verify', '--print-certs', apk, capture_output=True, text=True).stdout
        if f'Signer #1 certificate SHA-256 digest: {fingerprint}' not in output:
            raise ValueError(f'Original key does not match {apk}')
    directory.mkdir(mode=0o700, parents=True)
    password = secrets.token_urlsafe(48)
    password_file = directory / 'password'
    password_file.write_text(password + '\n')
    password_file.chmod(0o600)
    env['PIPBOY_RELEASE_PASSWORD'] = password
    run('keytool', '-genkeypair', '-keystore', directory / 'release.p12', '-storetype', 'PKCS12',
        '-storepass:env', 'PIPBOY_RELEASE_PASSWORD', '-keypass:env', 'PIPBOY_RELEASE_PASSWORD',
        '-alias', 'pipboy-release', '-keyalg', 'RSA', '-keysize', '4096', '-validity', '10950',
        '-dname', 'CN=Pip-Boy Release, O=and1gum', env=env)
    run(tool, 'rotate', '--out', directory / 'debug-to-release.lineage', '--old-signer',
        '--ks', old_key, '--ks-key-alias', 'androiddebugkey', '--ks-pass', 'env:PIPBOY_OLD_PASS',
        '--set-installed-data', 'true', '--set-rollback', 'false',
        '--new-signer', '--ks', directory / 'release.p12', '--ks-key-alias', 'pipboy-release',
        '--ks-pass', 'env:PIPBOY_RELEASE_PASSWORD', env=env)
    run('keytool', '-exportcert', '-rfc', '-keystore', directory / 'release.p12', '-alias', 'pipboy-release',
        '-storepass:env', 'PIPBOY_RELEASE_PASSWORD', '-file', directory / 'release-certificate.pem', env=env)
    (directory / 'debug-certificate.sha256').write_text(fingerprint + '\n')
    for path in directory.iterdir():
        path.chmod(0o600)
    shutil.copytree(directory, backup)
    for path in directory.iterdir():
        if path.read_bytes() != (backup / path.name).read_bytes():
            raise RuntimeError('Signing backup verification failed')
    backup.chmod(0o700)
    print(f'Signing key: {directory}\nVerified independent backup: {backup}')


def sign(directory, source, target):
    directory = Path(directory).expanduser()
    env = dict(os.environ, PIPBOY_RELEASE_PASSWORD=(directory / 'password').read_text().strip())
    tool = Path(os.environ['ANDROID_HOME']) / 'build-tools/35.0.0/apksigner'
    run(tool, 'sign', '--ks', directory / 'release.p12', '--ks-key-alias', 'pipboy-release',
        '--ks-pass', 'env:PIPBOY_RELEASE_PASSWORD', '--lineage', directory / 'debug-to-release.lineage',
        '--rotation-min-sdk-version', '33', '--v1-signing-enabled', 'false', '--v2-signing-enabled', 'false',
        '--v3-signing-enabled', 'true', '--v4-signing-enabled', 'false', '--out', target, source, env=env)
    run(tool, 'verify', '--verbose', '--print-certs', target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--signing-dir', default=os.environ.get('PIPBOY_SIGNING_DIR', str(Path.home() / '.local/share/pip-boy-signing')))
    commands = parser.add_subparsers(dest='command', required=True)
    setup = commands.add_parser('init')
    setup.add_argument('--backup-dir', required=True)
    setup.add_argument('--old-key', required=True)
    setup.add_argument('--reference-apk', action='append', required=True)
    signer = commands.add_parser('sign')
    signer.add_argument('source')
    signer.add_argument('target')
    args = parser.parse_args()
    if args.command == 'init':
        init(args.signing_dir, args.backup_dir, args.old_key, args.reference_apk)
    else:
        sign(args.signing_dir, args.source, args.target)


if __name__ == '__main__':
    main()
