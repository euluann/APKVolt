# encoding: utf-8
# Copyright (c) 2026 Luan Pestana
# SPDX-License-Identifier: MIT

# Classe de excecoes principal do apkvolt
class APKVoltError(Exception):
	pass

# Classe de excecoes de alinhamento apk do apkvolt
class APKAlignError(APKVoltError):
	pass

# Classe de excecoes de assinamento apk do apkvolt
class APKSignError(APKVoltError):
	pass

# Classe de excecoes do apkforge do apkvolt
class APKForgeError(APKVoltError):
	pass

# Classe de excecoes do logger do apkvolt
class LoggerError(APKVoltError):
	pass

# Classe de excecao do python3.11 faltando
class MissingPython311Error(APKVoltError):
	pass