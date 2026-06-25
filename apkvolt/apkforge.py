# encoding: utf-8
# Copyright (c) 2026 Luan Pestana
# SPDX-License-Identifier: MIT

import pyaxml
import subprocess
import os
from .logger import logger
from .exceptions import APKVoltError, APKAlignError, APKSignError, APKForgeError
import re
import shutil
import sys
import datetime
from . import zipalign
from PIL import Image

# Funcao global que verifica se o java esta disponivel no path
def has_java():
	try: # Tenta chamar o java e perguntar a versao
		subprocess.run(
			["java", "-version"],
			stdout=subprocess.DEVNULL,
			stderr=subprocess.DEVNULL,
			check=True
		)
	except (FileNotFoundError, subprocess.CalledProcessError): # Se nao encontrou o java, emite erro
		sys.exit("Java is not installed or is not available in PATH.")


# Resolucao de cada icone para cada DPI
icon_sizes = {
	"mdpi": {
		"ic_launcher": (48, 48),
		"ic_launcher_background": (108, 108),
		"ic_launcher_foreground": (108, 108),
	},
	"hdpi": {
		"ic_launcher": (72, 72),
		"ic_launcher_background": (162, 162),
		"ic_launcher_foreground": (162, 162),
	},
	"xhdpi": {
		"ic_launcher": (96, 96),
		"ic_launcher_background": (216, 216),
		"ic_launcher_foreground": (216, 216),
	},
	"xxhdpi": {
		"ic_launcher": (144, 144),
		"ic_launcher_background": (324, 324),
		"ic_launcher_foreground": (324, 324),
	},
	"xxxhdpi": {
		"ic_launcher": (192, 192),
		"ic_launcher_background": (432, 432),
		"ic_launcher_foreground": (432, 432),
	},
}

# Gera a arvore de icones em diferentes dimensoes apartir da dpi
def generate_asset(ic_launcher=None, ic_launcher_background=None, ic_launcher_foreground=None, presplash=None, output=""):
	
	# Se o caminho do icone principal doi especificado
	if ic_launcher is not None:
		# Abre a imagem
		with Image.open(ic_launcher) as img:
			# Converte para RGBA para armazenar Alpha
			img = img.convert("RGBA")
			
			# Percorre todas as dpi's do dicionario icon_sizes
			for dpi in list(icon_sizes.keys()):
				
				# Cria as pastas para os icones da respectiva dpi
				os.makedirs(os.path.join(output, f"res/mipmap-{dpi}-v4"), exist_ok=True)
				
				# Percorre todos os nomes de icones do dicionario icon_sizes
				for icon_name in list(icon_sizes[dpi].keys()):
					
					# Obtem as dimensoes ideais do icone para a dpi
					size = icon_sizes[dpi][icon_name]
					
					# Redimensiona a imagem
					new_img = img.resize(size, Image.LANCZOS)
					
					# Salva a imagem redimensionada
					new_img.save(os.path.join(output, f"res/mipmap-{dpi}-v4/{icon_name}.png"))
	
	# Se o caminho do icone de fundo doi especificado
	if ic_launcher_background is not None:
		# Abre a imagem
		with Image.open(ic_launcher_background) as img:
			# Converte para RGBA para armazenar Alpha
			img = img.convert("RGBA")
			
			# Percorre todas as dpi's do dicionario icon_sizes
			for dpi in list(icon_sizes.keys()):
				# Cria as pastas para os icones da respectiva dpi
				os.makedirs(os.path.join(output, f"res/mipmap-{dpi}-v4"), exist_ok=True)
				
				# Obtem as dimensoes ideais do icone para a dpi
				size = icon_sizes[dpi]["ic_launcher_background"]
				
				# Redimensiona a imagem
				new_img = img.resize(size, Image.LANCZOS)
				
				# Salva a imagem redimensionada
				new_img.save(os.path.join(output, f"res/mipmap-{dpi}-v4/ic_launcher_background.png"))
	
	# Se o caminho do icone de primeiro plano foi especificado
	if ic_launcher_foreground is not None:
		# Abre a imagem
		with Image.open(ic_launcher_foreground) as img:
			# Converte para RGBA para armazenar Alpha
			img = img.convert("RGBA")
			
			# Percorre todas as dpi's do dicionario icon_sizes
			for dpi in list(icon_sizes.keys()):
				# Cria as pastas para os icones da respectiva dpi
				os.makedirs(os.path.join(output, f"res/mipmap-{dpi}-v4"), exist_ok=True)
				
				# Obtem as dimensoes ideais do icone para a dpi
				size = icon_sizes[dpi]["ic_launcher_foreground"]
				
				# Redimensiona a imagem
				new_img = img.resize(size, Image.LANCZOS)
				
				# Salva a imagem redimensionada
				new_img.save(os.path.join(output, f"res/mipmap-{dpi}-v4/ic_launcher_foreground.png"))
		
	
	# Se o caminho da imagem de carregamento foi especificado
	if presplash is not None:
		# Abre a imagem
		with Image.open(presplash) as img:
			# Converte para RGBA para armazenar Alpha
			img = img.convert("RGBA")
			
			# Cria a pasta para armazenar o drawable
			os.makedirs(os.path.join(output, f"res/drawable"), exist_ok=True)
			
			# Salva a imagem redimensionada
			img.save(os.path.join(output, f"res/drawable/presplash.png"))
			

# Classe de comandos apk
class APK:
	# Funcao para alinha o apk com zipalign
	@staticmethod
	def aligner(apk_path):
		# Obtem o diretorio do apk alinhado
		apk_aligned_path = apk_path.replace(".apk", "-aligned.apk")
		
		zipalign.align(
			apk_path,
			apk_aligned_path,
			alignment=4,
			so_alignment=4096
		)# Comando para alinhar o apk com o alinhamento desejado pelo android
		
		os.replace(apk_aligned_path, apk_path) # Substitue o apk nao alinhado pelo alinhado
	
	# Funcao para assinar o apk com apksigner
	@staticmethod
	def signer(apk_path, keystore_path, key_alias, keystore_pass=None, key_pass=None):
		has_java() # Verifica se o java esta disponivel
		if keystore_path != None:
			if not os.path.exists(keystore_path):
				raise APKSignError(f" Keystore Path not found: {keystore_path}")
		# Obtem o diretorio com o script atual
		script_path = os.path.realpath(__file__)
		# Obtem o diretorio onde o script esta
		script_dir = os.path.dirname(script_path)
		apksigner_path = os.path.join(script_dir, "toolchain/apksigner.jar")
		cmd = [
			"java",
			"-jar",
			apksigner_path,
			"sign",
			"--ks", keystore_path,
			"--ks-key-alias", key_alias,
		] # Comando para assinar o apk
		
		if keystore_pass: # Se uma senha para a keystore for especificada
			# Adiciona o argumento para especificar a senha
			cmd.append("--ks-pass")
			cmd.append(f"pass:{keystore_pass}")
		
		if key_pass: # Se uma senha para a chave for especificada
			# Adiciona o argumento para especificar a senha
			cmd.append("--key-pass")
			cmd.append(f"pass:{key_pass}")
		
		cmd.append(apk_path) # Adiciona o argumento para especificar o caminho do apk
		
		# Executa o comando para assinar o apk
		result = subprocess.run(cmd, capture_output=True, text=True)
		
		if result.returncode != 0: # Se houve problemas na assinatura
			logger.error("Apksigner error")
			raise APKSignError(f"Apksigner error:\n{result.stderr}")

# Classe de comandos axml
class AXML:
	# Tipos de dados
	TYPE_STRING = 0x03
	TYPE_INT_DEC = 0x10
	TYPE_INT_HEX = 0x11
	TYPE_INT_BOOLEAN = 0x12
	TYPE_REFERENCE = 0x01
	
	# Inicia a classe, abre, e le os dados do axml
	def __init__(self, axml_path):
		self.axml_path = axml_path
		self._open_axml()
	
	# Abre o arquivo axml e salva na classe seus dados internos
	def _open_axml(self):
		if not os.path.exists(self.axml_path): # Mostra um erro se o caminho do axml nao existir
			logger.error("AXML path not found")
			raise APKForgeError("AXML path not found")
		
		with open(self.axml_path, "rb") as file: # Abre o aquivo axml
			self.axml_data = file.read() # Le os dados
		
		# Utilizar o decodificador automatico do pyaxml para interpretar como arsc
		self.axml_object, self.t = pyaxml.AXMLGuess.from_axml(self.axml_data)
		
		# Verifica a codificação
		self.flags = self.axml_object.proto.stringblocks.hnd.flag
		if (self.flags & 0x100) != 0:
			self.code = 'utf-8'
		else:
			self.code = 'utf-16le'
		
		# Salvar as chunks do axml
		self.chunks = self.axml_object.proto.resourcexml.elts
		# Salvar a tabela de strings do axml
		self.string_table = self.axml_object.proto.stringblocks.stringblocks
	
	# Abre o arquivo axml novo e salva nele seus dados internos apos as modificacoes
	def save(self):
		self.axml_object.compute() # Recalcula offsets/chunks
				
		new_axml_data = self.axml_object.pack() # Empacota
		
		with open(self.axml_path, "wb") as file: # Abre o aquivo axml
			file.write(new_axml_data) # Salva os dados novos do axml
			
	# Modifica booleanos especificos no axml
	def set_bool_attribute(self, bool_name, boolean, tag_name=None, replace_all=False):
		# bool_name - Nome do booleano a ser modificado
		# boolean - Novo booleano do atributo
		# replace_all - Se todas as strings identicas a old_string seram substituidas pela new_string
		# tag_name - Nome de uma tag especifica para procurar
		
		if not isinstance(boolean, bool): # Mostra um erro se o valor nao for booleano
			logger.error("Attribute value must be a boolean")
			raise APKForgeError("Attribute value must be a boolean")
		
		attribute_found = False # Variavel que alerta se algum atributo foi encontrado
		attribute_type_found = False # Variavel que alerta se algum atributo do tipo certo foi encontrado
		modified = False # Variavel que alerta se algum atributo foi modificado
		
		# _____ Procura o atributo que sera modificado _____
		
		# Percorrer todas as chunks
		for c in range(len(self.chunks)):
			# Se a tag start_elt nao existir nessa chunk, ela eh pulada
			if self.chunks[c].header.type != pyaxml.RES_XML_START_ELEMENT_TYPE:
				continue
			# Salvar a tag start_elt
			tag = self.chunks[c].start_elt
			
			# Se um nomd de tag foi especificado e a tag atual do loop nao tem o nome especificado, ela eh pulada
			if tag_name is not None:
				if self.string_table[tag.name].data.decode(self.code) != tag_name:
					continue
			# Percorrer todos os atributos da tag start_elt
			for a in range(len(tag.attributes)):
				# Salva o atributo atual do loop
				attr = tag.attributes[a]
				# Se o atributo atual do loop tem o nome especificado
				if self.string_table[attr.name].data.decode(self.code) == bool_name:
					attribute_found = True # Alerta ter encontrado o atributo
					# Salva o tipo dos dados do atributo
					raw = attr.type
					data_type = (raw >> 24) & 0xFF
					# Atualiza o valor de acordo com o tipo de dado
					if data_type == self.TYPE_INT_BOOLEAN:
						attribute_type_found = True # Alerta ter encontrado o atributo do tipo certo
						if  boolean:
							# Atualiza o valor do atributo
							attr.data = 0xFFFFFFFF
						else:
							# Atualiza o valor do atributo
							attr.data = 0x00000000
						# Alerta atualizacao
						modified = True
				if not replace_all and modified: # Quebra o loop no primeiro atributo modificadoF
					break
			if not replace_all and modified: # Quebra o loop no primeiro atributo modificado
				break
				
		
		if not attribute_found:
			logger.error("Attribute not found")
			raise APKForgeError("Attribute not found")
		if not attribute_type_found:
			logger.error("Attribute type must be a boolean")
			raise APKForgeError("Attribute type must be a boolean")
			
	# Modifica inteiros especificos no axml
	def set_int_attribute(self, int_name, value, tag_name=None, replace_all=False):
		# int_name - Nome do inteiro a ser modificado
		# value - Novo valor do atributo
		# replace_all - Se todas as strings identicas a old_string seram substituidas pela new_string
		# tag_name - Nome de uma tag especifica para procurar
		
		not_int = False
		# Se nao for um inteiro
		if not isinstance(value, int):
			# Se for uma string
			if isinstance(value, str):
				# Tenta converter para um inteiro
				try:
					value = int(value)
				except ValueError:
					not_int = True # Se nao for digito nem inteiro
			else:
				not_int = True # Se nao for str nem inteiro
		if not_int: # Mostra um erro se o valor nao for inteiro
			logger.error("Attribute value must be an integer")
			raise APKForgeError("Attribute value must be an integer")
		
		attribute_found = False # Variavel que alerta se algum atributo foi encontrado
		attribute_type_found = False # Variavel que alerta se algum atributo do tipo certo foi encontrado
		modified = False # Variavel que alerta se algum atributo foi modificado
		
		# _____ Procura o atributo que sera modificado _____
		
		# Percorrer todas as chunks
		for c in range(len(self.chunks)):
			# Se a tag start_elt nao existir nessa chunk, ela eh pulada
			if self.chunks[c].header.type != pyaxml.RES_XML_START_ELEMENT_TYPE:
				continue
			# Salvar a tag start_elt
			tag = self.chunks[c].start_elt
			
			# Se um nomd de tag foi especificado e a tag atual do loop nao tem o nome especificado, ela eh pulada
			if tag_name is not None:
				if self.string_table[tag.name].data.decode(self.code) != tag_name:
					continue
			# Percorrer todos os atributos da tag start_elt
			for a in range(len(tag.attributes)):
				# Salva o atributo atual do loop
				attr = tag.attributes[a]
				# Se o atributo atual do loop tem o nome especificado
				if self.string_table[attr.name].data.decode(self.code) == int_name:
					attribute_found = True # Alerta ter encontrado o atributo
					# Salva o tipo dos dados do atributo
					raw = attr.type
					data_type = (raw >> 24) & 0xFF
					# Atualiza o valor de acordo com o tipo de dado
					if data_type == self.TYPE_INT_DEC or data_type == self.TYPE_INT_HEX:
						attribute_type_found = True # Alerta ter encontrado o atributo do tipo certo
						# Atualiza o valor do atributo
						attr.data = value
						# Alerta atualizacao
						modified = True
					if data_type == self.TYPE_STRING: # Se for do tipo string
						new_string = str(value) # Converte valor para string
						attribute_type_found = True # Alerta ter encontrado o atributo do tipo certo
						
						# Atualiza a string na tabela de strings identificando a mesma pelo value do atributo
						self.string_table[attr.value].data = new_string.encode(self.code)
						# Atualiza o tamanho da string na tabela de string
						self.string_table[attr.value].size = len(new_string)
						# Alerta atualizacao
						modified = True
				if not replace_all and modified: # Quebra o loop no primeiro atributo modificadoF
					break
			if not replace_all and modified: # Quebra o loop no primeiro atributo modificado
				break
				
		
		if not attribute_found:
			logger.error("Attribute not found")
			raise APKForgeError("Attribute not found")
		if not attribute_type_found:
			logger.error("Attribute type must be an integer")
			raise APKForgeError("Attribute type must be an integer")
			
	
	# Modifica strings especificas no axml
	def set_string_attribute(self, str_name, new_string, tag_name=None, replace_all=False):
		# str_name - Nome do inteiro a ser modificado
		# new_string - Nova string do atributo
		# replace_all - Se todas as strings identicas a old_string seram substituidas pela new_string
		# tag_name - Nome de uma tag especifica para procurar
		
		if not isinstance(new_string, str): # Mostra um erro se string nao for uma string
			logger.error("Attribute string must be a string")
			raise APKForgeError("Attribute string must be a string")
		
		attribute_found = False # Variavel que alerta se algum atributo foi encontrado
		attribute_type_found = False # Variavel que alerta se algum atributo do tipo certo foi encontrado
		modified = False # Variavel que alerta se algum atributo foi modificado
		
		# _____ Procura o atributo que sera modificado _____
		
		# Percorrer todas as chunks
		for c in range(len(self.chunks)):
			# Se a tag start_elt nao existir nessa chunk, ela eh pulada
			if self.chunks[c].header.type != pyaxml.RES_XML_START_ELEMENT_TYPE:
				continue
			# Salvar a tag start_elt
			tag = self.chunks[c].start_elt
			
			# Se um nomd de tag foi especificado e a tag atual do loop nao tem o nome especificado, ela eh pulada
			if tag_name is not None:
				if self.string_table[tag.name].data.decode(self.code) != tag_name:
					continue
			# Percorrer todos os atributos da tag start_elt
			for a in range(len(tag.attributes)):
				# Salva o atributo atual do loop
				attr = tag.attributes[a]
				# Se o atributo atual do loop tem o nome especificado
				if self.string_table[attr.name].data.decode(self.code) == str_name:
					attribute_found = True # Alerta ter encontrado o atributo
					if attr.value == 0xFFFFFFFF:
						continue
					# Salva o tipo dos dados do atributo
					raw = attr.type
					data_type = (raw >> 24) & 0xFF
					# Atualiza o valor de acordo com o tipo de dado
					if data_type == self.TYPE_STRING:
						attribute_type_found = True # Alerta ter encontrado o atributo do tipo certo
						
						# Atualiza a string na tabela de strings identificando a mesma pelo value do atributo
						self.string_table[attr.value].data = new_string.encode(self.code)
						# Atualiza o tamanho da string na tabela de string
						self.string_table[attr.value].size = len(new_string)
						# Alerta atualizacao
						modified = True
				if not replace_all and modified: # Quebra o loop no primeiro atributo modificadoF
					break
			if not replace_all and modified: # Quebra o loop no primeiro atributo modificado
				break
				
		
		if not attribute_found:
			logger.error("Attribute not found")
			raise APKForgeError("Attribute not found")
		if not attribute_type_found:
			logger.error("Attribute type must be a string")
			raise APKForgeError("Attribute type must be a string")
	

# Classe de comandos arsc
class ARSC:
	# Tipos de dados
	TYPE_STRING = 0x03
	TYPE_INT_DEC = 0x10
	TYPE_INT_HEX = 0x11
	TYPE_INT_BOOLEAN = 0x12
	TYPE_REFERENCE = 0x01
	
	# Inicia a classe, abre, e le os dados do arsc
	def __init__(self, arsc_path):
		# arsc_path - Caminho para o arquivo arsc
		self.arsc_path = arsc_path
		self._open_arsc()
	
	# Funcao para abrir arquivo arsc e armazenar os dados
	def _open_arsc(self):
		if not os.path.exists(self.arsc_path): # Mostra um erro se o caminho do axml nao existir
			logger.error("ARSC path not found")
			raise APKForgeError("ARSC path not found")
		
		with open(self.arsc_path, "rb") as file: # Abre o aquivo axml
			self.arsc_data = file.read() # Le os dados
		# Utilizar o decodificador automatico do pyaxml para interpretar como arsc
		self.arsc_object, self.t = pyaxml.AXMLGuess.from_axml(self.arsc_data)
		
		# Verifica a codificação
		self.flags = self.arsc_object.proto.stringblocks.hnd.flag
		if (self.flags & 0x100) != 0:
			self.code = 'utf-8'
		else:
			self.code = 'utf-16le'
			
		# Salvar as chunks de packages do axml
		self.chunks = self.arsc_object.proto.restablespackage
		# Salvar a tabela de strings do axml
		self.string_table = self.arsc_object.proto.stringblocks.stringblocks# Salvar as chunks do axml
	
	# Identifica e obtem o package
	def _get_package(self, package_index):
		package = None
		# Percorre todas as chunks do arsc
		for i in range(len(self.chunks)):
			# Identifica o package nas chunks pelo package_index
			if self.chunks[i].id == package_index:
				package = self.chunks[i]
				
		if package is None: # Verifica se o package especificado foi encontrado
			logger.error("Package not found")
			raise APKForgeError("Package not found")
		return package
	
	def _get_package_chunck_index(self, package_index):
		package_chunk_index = None
		# Percorre todas as chunks do arsc
		for i in range(len(self.chunks)):
			# Identifica o package nas chunks pelo package_index
			if self.chunks[i].id == package_index:
				package_chunk_index = i
		
		if package_chunk_index is None: # Verifica se o package especificado foi encontrado
			logger.error("Package not found")
			raise APKForgeError("Package not found")
		return package_chunk_index
				
		if package_index is None: # Verifica se o package especificado foi encontrado
			logger.error("Package not found")
			raise APKForgeError("Package not found")
		
	# Divide res_id
	def _split_res_id(self, res_id):
		package_index = (res_id >> 24) & 0xFF # Extrai o packagex_index, para identificar o package
		type_index = (res_id >> 16) & 0xFF # Extrai o type_index, para identificar o tipo do resource
		entry_index = res_id & 0xFFFF # Extrai o entry_index, para identificar o resource dentro do pacote e tipo especifico
		
		return package_index, type_index, entry_index
	# Funcao para mostrar um resource especifico dentro do arsc
	def show_res(self, res_id):
		
		package_index, type_index, entry_index = self._split_res_id(res_id) # Divide os indices
		
		package = self._get_package(package_index) # Identifica e obtem o package
		
		resource_type_found = False
		# Percorre todos os tipos de resources
		for restype in package.restypes:
			# Pula a execução atual do loop se não houver o campo typetype
			# Alguns chunks são apenas typespec e não possuem dados de recursos.
			if not restype.HasField("typetype"):
				continue
			# Se o resource da execucao atual do loop for do tipo especificado
			if restype.typetype.id == type_index:
				resource_type_found = True # Alerta ter encontrado o resource do tipo especificado
				
				if entry_index >= len(restype.typetype.tables): # Se o entry_index for maior que a quantidade de resources
					logger.error("Resource index not found")
					raise APKForgeError("Resource index not found")
				if not restype.typetype.tables[entry_index].present: # Verifica se o resource esta vazio
					logger.error("Resource entry is empty")
					raise APKForgeError("Resource entry is empty")
				# Verifica o tipo de informacao contida no resource para evitar erros, e imprime na tela
				if restype.typetype.tables[entry_index].key.data_type == self.TYPE_STRING:
					print(f"Type: {self.TYPE_STRING}")
					print(self.string_table[restype.typetype.tables[entry_index].key.data])
				else:
					print(f"Type: {restype.typetype.tables[entry_index].key.data_type}")
					print(restype.typetype.tables[entry_index])
					
		if not resource_type_found: # Verifica se o resource do tipo especificado nao foi encontrado
			logger.error("Resource type not found")
			raise APKForgeError("Resource type not found")
	
	# Funcao para modificar o package
	def set_package(self, package_id, new_package):
		
		package_chunk_index = self._get_package_chunck_index(package_id) # Identifica o indice do package nos ckunks
		
		if not re.fullmatch(r"[A-Za-z0-9_.]+", new_package):
			logger.error("Invalid package name")
			raise APKForgeError("Invalid package name")
			
		if len(new_package) > 128: # Verifica se ele tem mais de 128 bytes de tamanho
			logger.error("New Package too long")
			raise APKForgeError("New Package too long")
		
		new_package_padding = new_package + "\0"*(128-len(new_package)) # Aplica padding de bytes nulos para ter perfeitamente 128 bytes de tamanho
		
		self.chunks[package_chunk_index].name = new_package_padding # Define o novo package
		
	# Funcao para modificar um resource especifico dentro do arsc
	def set_string_res(self, res_id, new_res, config_index=0):
		# config_index - Se None, modificara todos os resources correspondente ao res_id independente do config
		
		package_index, type_index, entry_index = self._split_res_id(res_id) # Divide os indices
		
		package = self._get_package(package_index) # Identifica e obtem o package
		
		resource_type_found = False
		resource_typetype_found = False
		config_i = 0
		# Percorre todos os tipos de resources
		for restype in package.restypes:
			# Pula a execução atual do loop se não houver o campo typetype
			# Alguns chunks são apenas typespec e não possuem dados de recursos.
			if not restype.HasField("typetype"):
				continue
			# Se o resource da execucao atual do loop for do tipo especificado
			if restype.typetype.id == type_index:
				resource_type_found = True # Alerta ter encontrado o resource do tipo especificado
				
				if entry_index >= len(restype.typetype.tables): # Se o entry_index for maior que a quantidade de resources
					logger.error("Resource index not found")
					raise APKForgeError("Resource index not found")
				if not restype.typetype.tables[entry_index].present: # Verifica se o resource esta vazio
					logger.error("Resource entry is empty")
					raise APKForgeError("Resource entry is empty")
				# Verifica o tipo de informacao contida no resource para evitar erros, e imprime na tela
				if restype.typetype.tables[entry_index].key.data_type == self.TYPE_STRING:
					if config_index == config_i or config_index is None: # Verifica se o index do config eh o especificado ou se nao ha especificacao
						new_res = str(new_res)
						self.string_table[restype.typetype.tables[entry_index].key.data].data = new_res.encode(self.code) # Atualiza a string
						self.string_table[restype.typetype.tables[entry_index].key.data].size = len(new_res) # Atualiza o tamanho de caracteres da string
						self.string_table[restype.typetype.tables[entry_index].key.data].redundant_size = len(new_res.encode(self.code)) # Atualiza o tamanho de bytes da string
						resource_typetype_found = True
				config_i += 1
					
		if not resource_typetype_found: # Verifica se o resource encontrado nao eh do tipo especificado
			logger.error("Resource found is not a string")
			raise APKForgeError("Resource found is not a string")
		if not resource_type_found: # Verifica se o resource do tipo especificado nao foi encontrado
			logger.error("Resource type not found")
			raise APKForgeError("Resource type not found")
	# Abre o arquivo arsc novo e salva nele seus dados internos apos as modificacoes
	def save(self):
		self.arsc_object.compute() # Recalcula offsets/chunks
				
		new_arsc_data = self.arsc_object.pack() # Empacota
		
		with open(self.arsc_path, "wb") as file: # Abre o aquivo axml
			file.write(new_arsc_data) # Salva os dados novos do axml

# Classe de comandos dex
class DEX:
	# Inicia a classe e descompila o arquivo dex
	def __init__(self, dex_path):
		has_java() # Verifica se o java esta disponivel
		# dex_path - Caminho para o arquivo arsc
		self.dex_path = dex_path
		self._decompile_dex()
	
	# Funcao para descompilar arquivo dex e armazenar os dados
	def _decompile_dex(self):
		self.closed = False
		
		if not os.path.exists(self.dex_path): # Mostra um erro se o caminho do axml nao existir
			logger.error("DEX path not found")
			raise APKForgeError("DEX path not found")
		# Obtem o diretorio com o script atual
		script_path = os.path.realpath(__file__)
		# Obtem o diretorio onde o script esta
		script_dir = os.path.dirname(script_path)
		# Obtem o diretorio onde o baksmali.jar esta
		baksmali_path = os.path.join(script_dir, "toolchain/baksmali.jar")
		# Obtem o diretorio onde sera descompilado o dex
		dex_name = os.path.splitext(os.path.basename(self.dex_path))[0]
		smali_dir_name = datetime.datetime.now().strftime(f".cache_{dex_name}_smali_%Y%m%d_%H%M%S_%f") # Gera o nome da pasta onde ficara o dex descompilado, com ano, mes, dia, hora, minuto, segundos e milisegundos, para evitar colisoes ao abrir varios dex
		self.smali_dir = os.path.join(os.path.dirname(self.dex_path), ".apkforge_dexcache", smali_dir_name)
		cmd = [
			"java",
			"-jar",
			baksmali_path,
			"d",
			self.dex_path,
			"-o",
			self.smali_dir
		] # Comando para descompilar o dex para smali
		
		# Executa o comando para descompilar o dex para smali
		result = subprocess.run(cmd, capture_output=True, text=True)
		
		if result.returncode != 0: # Se houve problemas no comando
			logger.error("Baksmali error")
			raise APKForgeError(f"Baksmali error:\n{result.stderr}")
	
	# Funcao para explorar todas as subpastas de uma pasta, retornando apenas subpastas que tem arquivos smali
	def _smali_path_finder(self, path):
		results = []
		
		# Percorre todas as subpastas da pasta atual
		for item in os.listdir(path):
			# Obtem o caminho completo
			full_path = os.path.join(path, item)
			# Se o item atual do loop for uma pasta
			if os.path.isdir(full_path):
				# Explora todas as subpastas da pasta atual do loop e extende o results ao resultado do path finder
				results.extend(self._smali_path_finder(full_path))
			
			# Verifica se a pasta atual contem arquivos smali
			if full_path.endswith(".smali"):
				if path not in results: # Se o path nao ja estiver em results
					results.append(path) # Adiciona o path em results
				
		return results
		
	# Funcao para detectar os packages do dex
	def _find_package(self):
		# Percorre todas as subpastas descompiladas do dex para identificar o package com base no nome dos diretorios
		packages = self._smali_path_finder(self.smali_dir)
		
		# Percorre todos os packages identificados para tirar o caminho completo das pastas do package para deixar so o package
		for i in range(len(packages)):
			pack = packages[i]
			packages[i] = os.path.relpath(pack, self.smali_dir)
			
		return packages
	
	# Mostra todos os packages do dex
	def show_packages(self):
		if self.closed:
			logger.error("Closed dex error")
			raise APKSignError(f"Closed dex error")
		print(self._find_package())
	
	# Define um package do dex
	def set_package(self, package_index, new_package):
		if self.closed:
			logger.error("Closed dex error")
			raise APKSignError(f"Closed dex error")
			
		packages = self._find_package() # Identifica todos os packages do dex
		if not packages: # Verifica se nenhum package foi encontrado
			logger.error("No DEX package found")
			raise APKForgeError("No DEX package found")
		if not (-len(packages) <= package_index < len(packages)): # Verifica se o package_index eh invalido pra lista packages
			logger.error("DEX package index out of range")
			raise APKForgeError("DEX package index out of range")
		
		if not re.fullmatch(r"[A-Za-z0-9_.]+", new_package):
			logger.error("Invalid package name")
			raise APKForgeError("Invalid package name")
			
		if len(new_package) > 128: # Verifica se ele tem mais de 128 bytes de tamanho
			logger.error("New Package too long")
			raise APKForgeError("New Package too long")
		
		new_package = new_package.replace('.', '/') # Converte os pontos do package em barras, o formato que o smali exige
		old_package = packages[package_index] # Obtem o package antigo
		
		# Obtem os diretorios dos packages
		old_package_dir = os.path.join(self.smali_dir, old_package)
		new_package_dir = os.path.join(self.smali_dir, new_package)
		
		# Cria as pastas do novo package
		os.makedirs(new_package_dir, exist_ok=True)
		
		# Percorre todos os itens do diretorio do package antigo
		for item in os.listdir(old_package_dir):
			shutil.move(
				os.path.join(old_package_dir, item),
				os.path.join(new_package_dir, item)
			) # Move todos os itens do diretorio do package antigo para o novo
		
		# Percorre todas as pastas do dex descompilado, das mais profundas para as mais rasas
		for root, dirs, files in os.walk(self.smali_dir, topdown=False):
			# Deleta elas se vazias
			if not os.listdir(root):
				os.rmdir(root)
		
		# Percorre todos os arquivos do dex descompilado
		for root, dirs, files in os.walk(self.smali_dir):
				for file in files:
					# Obtem o caminho do arquivo
					file_path = os.path.join(root, file)
					# Se eh um arquivo smali
					if file.endswith(".smali"):
						# Abre como leitura
						with open(file_path, 'r') as smali_file:
							# Le o conteudo arquivo e substitue todas as mencoes do package antigo para o package novo
							smali_content = smali_file.read()
							smali_content = smali_content.replace(old_package, new_package)
						# Escreve o conteudo modificado
						with open(file_path, 'w') as smali_file:
							smali_file.write(smali_content)
	
	# Funcao para compilar dex
	def save(self):
		if self.closed:
			logger.error("Closed dex error")
			raise APKForgeError(f"Closed dex error")
		
		# Obtem o diretorio com o script atual
		script_path = os.path.realpath(__file__)
		# Obtem o diretorio onde o script esta
		script_dir = os.path.dirname(script_path)
		# Obtem o diretorio onde o baksmali.jar esta
		smali_path = os.path.join(script_dir, "toolchain/smali.jar")
		cmd = [
			"java",
			"-jar",
			smali_path,
			"a",
			self.smali_dir,
			"-o",
			self.dex_path,
		] # Comando para compilar o smali para dex
		
		# Executa o comando para compilar o smali para dex
		result = subprocess.run(cmd, capture_output=True, text=True)
		
		if result.returncode != 0: # Se houve problemas no comando
			logger.error("Smali error")
			raise APKForgeError(f"Smali error:\n{result.stderr}")
			
	# Funcao para deletar o dex descompilado e fechar a classe
	def close(self):
		self.closed = True # Alerta que nao ha dex descompilado mais
		shutil.rmtree(self.smali_dir) # Deleta o dex descompilado