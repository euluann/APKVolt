# encoding: utf-8
# Copyright (c) 2026 Luan Pestana
# SPDX-License-Identifier: MIT

import logging
from .exceptions import LoggerError, APKVoltError

# Cria nivel SUCCESS entre INFO(20) e WARNING(30)
SUCCESS_LEVEL = 25

# Registra o nome do nivel
logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")

# Adiciona metodo .success()
def success(self, message, *args, **kwargs):
	if self.isEnabledFor(SUCCESS_LEVEL):
		self._log(SUCCESS_LEVEL, message, args, **kwargs)
	
# Injeta o metodo na classe Logger
logging.Logger.success = success

# Cria o logger
logger = logging.getLogger("apkvolt")

# Atribue o log level info
logger.setLevel(logging.INFO)

# Dicionario de log levels
LOG_LEVELS = {
	"DEBUG": logging.DEBUG,
	"INFO": logging.INFO,
	"SUCCESS": SUCCESS_LEVEL,
	"WARNING": logging.WARNING,
	"ERROR": logging.ERROR
}

# Funcao que retorna valor numerico de log level para o logger do apkvolt
def parse_log_level(log_level_name):
	# Poe log_level inteiro em upper case e identifica seu inteiro
	log_level = LOG_LEVELS.get(log_level_name.upper())
		
	# Se nao existir emite um erro
	if log_level is None:
		set_log_level("info")
		logger.error(f"Invalid log level name: {log_level_name}")
		raise LoggerError(f"Invalid log level name: {log_level_name}")
	
	return log_level

# Atribue o log level especificado no logger do apkvolt
def set_log_level(log_level_name):
	if log_level_name is None:
		log_level_name = "INFO"
	log_level = parse_log_level(log_level_name)
	logger.setLevel(log_level)
