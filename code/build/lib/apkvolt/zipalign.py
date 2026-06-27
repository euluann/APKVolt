#!/usr/bin/python3
# encoding: utf-8
# Copyright (c) 2026 Luan Pestana
# SPDX-License-Identifier: MIT

import struct
import argparse

# Estrutura Zip, cada arquivo comeca com o tamanho fixo de 30 bytes de informacoes (chamados de Local Header), seguido respectivamente do nome, do Extra Field, dos dados do arquivo, e por fim do Post Data (dados ou informacoes que vem depois dos dados do arquivo mas antes da proxima estrutura), cada arquico tem necessariamente um Local Header e um Central Directory ao final dos Local Headers
#	[Local Header] [tamanho fixo de 30 bytes de informacoes]
#	[Nome]
#	[Extra Field]
#	[dados]
#	[Post Data]
#	
#	[Local Header] [tamanho fixo de 30 bytes de informacoes]
#	[Nome]
#	[Extra Field]
#	[dados]
#	[Post Data]
#	
#	[Local Header] [tamanho fixo de 30 bytes de informacoes]
#	[Nome]
#	[Extra Field]
#	[dados]
#	[Post Data]
#	...
#
#
#	[Central Directory] [tamanho fixo de 46 bytes de informacoes]
#	[Nome]
#	[Extra Field]
#	[Comments]
#	
#	[Central Directory] [tamanho fixo de 46 bytes de informacoes]
#	[Nome]
#	[Extra Field]
#	[Comments]
#	
#	[Central Directory] [tamanho fixo de 46 bytes de informacoes]
#	[Nome]
#	[Extra Field]
#	[Comments]
#	...
#
#
#	[End Of Central Directory] [tamanho fixo de 22 bytes de informacoes]
#	[Comments]

# Sobre struct
# < - little endian
# I - interpretar 4 bytes
# H - Interpretar 2 bytes


########## Variaveis globais importantes ##########

# Formato para interpretar o Local Header do zip
local_header_format = "<IHHHHHIIIHH"
# Tamanho fixo do Local Header
local_header_fix_length = 30

# Formato para interpretar o Central Directory do zip
central_directory_format = "<IHHHHHHIIIHHHHHII"
# Tamanho fixo do Central Directory
central_directory_fix_length = 46

# Formato para interpretar o End Of Central Directory do zip
end_of_central_directory_format = "<IHHHHIIH"
# Tamanho fixo do End Of Central Directory
end_of_central_directory_fix_length = 22

# Assinaturas, usadas para identificar sua posicao no arquivo zip
local_header_signature = 0x04034B50
central_directory_signature = 0x02014B50
end_of_central_directory_signature = 0x06054B50


########## Funcao principal para alinhar zips ##########

def align(input_zip, output_zip, alignment=4, so_alignment=None):
	
	# Se um alinhamento especifico pra arquivos so nao foi especificado
	if so_alignment is None:
		# O alinhamento para arquivos so sera exatamento o mesmo de todos os outros arquivos
		so_alignment = alignment
	
	# Abre o zip para leitura de bytes
	with open(input_zip, 'rb') as raw_zip:
		
		# offset - A posicao onde sera lida no zip
		offset = 0
		
		# Le todos os bytes do zip
		zip_data = raw_zip.read()
		
		# Armazena informacoes e offsets de cada arquivo para navegacao rapida
		entries = []
		
		# Armazena dados que vem depois dos dados comprimidos do arquivo e antes do proximo Local Header, para caso haja uma estrutura nova como Data Decryptor ou Apk Signing Block (bloco de assinatura do apk)
		post_data = {}
		
		# Dicionario temporario para o loop conseguir extrair o Post Data, para caso encontre dados entre os dados de um Local Header e o inicio do proximo Local Header, armazene o offset do inicio do Post Data e o nome do arquivo que o contem, ate achar o proximo Local header e junto o fim do Post Data
		post_data_temp = None
		
		# Percorre todos os bytes do zip, extraindo informacoes, Local Headers, Central Directorys e o End Of Central Directory
		while True:
			# Le a assinatura antes de interpretar os bytes seguintes
			signature = struct.unpack(
				'<I',
				zip_data[offset : offset + 4]
			)[0]
			
			# Se encontrar uma assinatura reconhecivel
			if signature in [local_header_signature, central_directory_signature, end_of_central_directory_signature]:
				# Se um Post Data foi encontrado antes da assinatura reconhecivel
				if post_data_temp is not None:
					# Identifica o nome do arquivo que tem Post Data
					filename = post_data_temp["filename"]
					
					# Identifica o offset do Post Data
					post_data_offset = post_data_temp["offset"]
					
					# Identifica o Post Data e armazena no dicionario de Post Datas
					post_data[filename] = zip_data[post_data_offset : offset]
					
					# Deleta os dados temporarios do Post Data que ja foi identificado e armazenado
					post_data_temp = None
			
			# Se for a assinatura do Local Header, os bytes seguintes seram interpretados como os de um Local Header
			if signature == local_header_signature:
				# Desempacota o Local Header inteiro em uma tupla
				local_header = struct.unpack(
					local_header_format,
					zip_data[offset : offset + local_header_fix_length]
				)
				# Quebra a tupla do Local Header em suas partes nomeadas e identificadas
				(
					signature,
					version,
					flags,
					compression,
					mod_time,
					mod_date,
					crc32,
					compressed_size,
					uncompressed_size,
					filename_length,
					extra_length
				) = local_header
				
				# Pula o offset para apos o Local Header
				offset += local_header_fix_length
				
				# Obtem o nome do arquivo, de forma que se o filename_length tem 19, obtem os 19 bytes seguinte o offset atual
				filename = zip_data[
					offset :
					offset +
					filename_length
				]
				
				# Pula o offset para apos o nome do arquivo
				offset += filename_length
				
				
				# Obtem os bytes extras do arquivo, de forma que se o extra_length tem 19, obtem os 19 bytes seguinte o offset atual
				extra = zip_data[
					offset :
					offset +
					extra_length
				]
				
				# Pula o offset para apos os bytes extras
				offset += extra_length
				
				# Pula o offset para apos os dados comprimidos do arquivo
				offset += compressed_size
				
				# Obtem a proxima assinatura
				next_signature = struct.unpack(
					'<I',
					zip_data[offset : offset + 4]
				)[0]
				
				# Se nao encontrar uma assinatura reconhecivel, significa inicio de um Post Data
				if next_signature not in [local_header_signature, central_directory_signature, end_of_central_directory_signature]:
					# Armazena os dados do inicio do Post Data
					post_data_temp = {"offset": offset, "filename": filename}
					
				
			# Se for a assinatura do Central Directory, os bytes seguintes seram interpretados como os de um Central Directory
			elif signature == central_directory_signature:
				# Desempacota o Central Directory inteiro em uma tupla
				central_directory = struct.unpack(
					central_directory_format,
					zip_data[offset : offset + central_directory_fix_length]
				)
				# Quebra a tupla do Central Directory em suas partes nomeadas e identificadas
				(
					signature,
					version_made_by,
					version_needed,
					flags,
					compression,
					mod_time,
					mod_date,
					crc32,
					compressed_size,
					uncompressed_size,
					filename_length,
					central_directory_extra_length,
					comment_length,
					disk_number,
					internal_attr,
					external_attr,
					local_header_offset
				) = central_directory
				
				central_directory_offset = offset
				
				# Pula o offset para apos o Central Directory
				offset += central_directory_fix_length
				
				# Obtem o nome do arquivo, de forma que se o filename_length tem 19, obtem os 19 bytes seguinte o offset atual
				filename = zip_data[
					offset :
					offset +
					filename_length
				]
				
				# Pula o offset para apos o nome do arquivo
				offset += filename_length
				
				# Pula o offset para apos os bytes extras
				offset += central_directory_extra_length
				
				# Extrai o comentario apos o Central Directory e o nome do arquivo
				comment = zip_data[
					offset :
					offset + comment_length
				]
				
				# Pula o offset para apos o comentario
				offset += comment_length
				
				# Calcula o offset onde comeca o nome do arquivo
				filename_offset = local_header_offset+local_header_fix_length
				
				# Obtem o nome do arquivo
				filename = zip_data[filename_offset : filename_offset + filename_length]
				
				# Obtem o comprimento do extra field do local_header do arquivo que o central directory se refere
				local_header_extra_length = struct.unpack(
					local_header_format,
					zip_data[
						local_header_offset :
						local_header_offset + local_header_fix_length
					]
				)[10]
				
				# Calcula o offset onde comeca os dados do arquivo
				data_offset = local_header_offset+local_header_fix_length+filename_length+local_header_extra_length
				
				# Adiciona ao entries todos os dados necessarios pra uma navegacao rapida
				entries.append(
					{
						"filename": filename,
						"central_directory_offset": central_directory_offset,
						"local_header_offset": local_header_offset,
						"data_offset": data_offset,
						"compressed_size": compressed_size,
						"local_header_extra_length": local_header_extra_length,
						"central_directory_extra_length": central_directory_extra_length,
						"filename_length": filename_length,
						"flags": flags,
						"comment": comment
					}
				)
				
				# Se o arquivo nao tiver Post Data identificado, armazena um Post Data vazio no dicionario 
				if filename not in post_data.keys():
					post_data[filename] = b""
				
			# Se for a assinatura do End Of Central Directory, os bytes seguintes seram interpretados como os de um End Of Central Directory
			elif signature == end_of_central_directory_signature:
				# Desempacota o End Of Central Directory inteiro em uma tupla
				end_of_central_directory = struct.unpack(
					end_of_central_directory_format,
					zip_data[offset : offset + end_of_central_directory_fix_length]
				)
				
				# Quebra a tupla do End Of Central Directory em suas partes nomeadas e identificadas
				(
					signature,
					disk_number,
					disk_start,
					entries_this_disk,
					total_entries,
					cd_size,
					cd_offset,
					comment_length
				) = end_of_central_directory
				
				# Armazena o offset do End Of Central Directory ao encontrar
				end_of_central_directory_offset = offset
				
				# Quebra o loop, pois chegou ao fim do arquico
				break
			else:
				# Se nao identificar uma assinatura reconhecivel, manda o offset para o byte seguinte ate achar uma assinatura reconhecivel, eh util para apks que tem paddings e um bloco de assinatura de apk (assinatura para o android baixar o apk) antes do Central Directory
				offset += 1
		
		# Cria o zip novo vazio que sera alinhado enquanto construido byte a byte
		with open(output_zip, 'wb') as zip:
			
			# Dicionario para armazenar os novos offsets de cada Local Header
			new_local_header_offset = {}
			
			# O offset para calculos
			offset = 0
			
			# Percorre os dados salvos de todos os arquivos dentro do zip, e escreve os Local Headers
			for data in entries:
				# Obtem o offset onde comeca o Local Header do arquivo atual
				local_header_offset = data["local_header_offset"]
				
				# Obtem o nome do arquivo atual
				filename = data["filename"]
				# Obtem o comprimento nome do arquivo atual
				filename_length = len(filename)
				
				# Obtem o comprimento do extra do Local Header arquivo atual
				extra_length = data["local_header_extra_length"]
				
				# Obtem o tamanho do arquico comprimido
				compressed_size = data["compressed_size"]
				
				# Armazena o offset novo do Local Header para atualizar o Central Directory futuramente
				new_local_header_offset[filename] = offset
				
				# Obtem os dados em bytes do Local Header
				local_header = zip_data[
					local_header_offset :
					local_header_offset +
					local_header_fix_length
				]
				# Obtem os dados em bytes do Extra Field
				extra = zip_data[
					local_header_offset +
					local_header_fix_length +
					filename_length :
					local_header_offset +
					local_header_fix_length +
					filename_length +
					extra_length
				]
				# Obtem os dados compridos em bytes do arquivo
				compressed_data = zip_data[
					local_header_offset +
					local_header_fix_length +
					filename_length +
					extra_length :
					local_header_offset +
					local_header_fix_length +
					filename_length +
					extra_length +
					compressed_size
				]
				
				# Obtem o offset dos dados do arquivo
				compressed_data_offset = (
					offset +
					local_header_fix_length +
					filename_length +
					extra_length
				)
				
				# Se nao for arquivo da pasta META-INF (pasta que armazena assinatura de um apk, que nao deve ser alinhada) e tambem nao for um arquivo so
				if not filename.startswith(b"META-INF") and not filename.endswith(b'.so'):
					# Calcula a quantidade de bytes nulos necessarios para o offset dos dados do arquivo ser multiplo de alignment (multiplo do alinhamento desejado)
					padding_length = (
						(alignment - (compressed_data_offset % alignment)) % alignment
					)
				# Se for um arquivo so (normalmente o android exige alinhamento diferente para arquivos so em apks)
				elif filename.endswith(b'.so'):
					# Calcula a quantidade de bytes nulos necessarios para o offset dos dados do arquivo ser multiplo de so_alignment (multiplo do alinhamento desejado para arquivos so)
					padding_length = (
						(so_alignment - (compressed_data_offset % so_alignment)) % so_alignment
					)
				else:
					# Se for um arquivo de META-INF, nao aplica nenhum alinhamento
					padding_length = 0
				
				# Cria o padding, bytes nulos na quantidade necessaria para o alinhamento 
				padding = b"\x00" * padding_length
				
				# Coloca o padding no Extra Field
				extra = extra + padding
				
				# Desempacota o Local Header inteiro em uma tupla
				local_header = struct.unpack(
					local_header_format,
					local_header
				)
				# Quebra a tupla do Local Header em suas partes nomeadas e identificadas
				(
					signature,
					version,
					flags,
					compression,
					mod_time,
					mod_date,
					crc32,
					compressed_size,
					uncompressed_size,
					filename_length,
					extra_length
				) = local_header
				
				# Atualiza o comprimento do Extra Field
				extra_length += padding_length
				
				# Empacota o Local Header inteiro em bytes novamente
				local_header = struct.pack(
					local_header_format,
						signature,
						version,
						flags,
						compression,
						mod_time,
						mod_date,
						crc32,
						compressed_size,
						uncompressed_size,
						filename_length,
						extra_length
				)
				
				# Atualiza o offset, somando todos os bytes percorridos, para que a proxima estrutura possa calcular corretamente os offsets
				offset = (
					offset +
					local_header_fix_length +
					filename_length +
					extra_length +
					compressed_size +
					len(post_data[filename])
				)
				
				# No zip novo
				# Escreve o Local Header
				zip.write(local_header)
				# Escreve o nome do arquivo
				zip.write(filename)
				# Escreve o Extra Field
				zip.write(extra)
				# Escreve os dados comprimidos do arquivo
				zip.write(compressed_data)
				# Escreve o Post Data
				zip.write(post_data[filename])
			
			new_central_directory_offset = offset
			# Percorre os dados salvos de todos os arquivos dentro do zip, e escreve os Central Directorys
			for data in entries:
				# Obtem o offset onde comeca o Central Directory do arquivo atual
				central_directory_offset = data["central_directory_offset"]
				
				# Obtem o nome do arquivo atual
				filename = data["filename"]
				# Obtem o comprimento nome do arquivo atual
				filename_length = len(filename)
				
				# Obtem o comprimento do extra do Central Directory arquivo atual
				extra_length = data["central_directory_extra_length"]
				
				# Obtem os comentarios do Central Directory arquivo atual
				comment = data["comment"]
				
				# Obtem os dados em bytes do Central Directory
				central_directory = zip_data[
					central_directory_offset :
					central_directory_offset +
					central_directory_fix_length
				]
				
				# Obtem os dados em bytes do Extra Field
				extra = zip_data[
					central_directory_offset +
					central_directory_fix_length +
					filename_length :
					central_directory_offset +
					central_directory_fix_length +
					filename_length +
					extra_length
				]
				
				# Desempacota o Central Directory inteiro em uma tupla
				central_directory = struct.unpack(
					central_directory_format,
					central_directory
				)
				
				# Quebra a tupla do Central Directory em suas partes nomeadas e identificadas
				(
					signature,
					version_made_by,
					version_needed,
					flags,
					compression,
					mod_time,
					mod_date,
					crc32,
					compressed_size,
					uncompressed_size,
					filename_length,
					central_directory_extra_length,
					comment_length,
					disk_number,
					internal_attr,
					external_attr,
					local_header_offset
				) = central_directory
				
				# Atualiza o offset do Local Header armazenado no Central Directory
				local_header_offset = new_local_header_offset[filename]
				
				# Empacota o Central Directory inteiro em bytes novamente
				central_directory = struct.pack(
					central_directory_format,
						signature,
						version_made_by,
						version_needed,
						flags,
						compression,
						mod_time,
						mod_date,
						crc32,
						compressed_size,
						uncompressed_size,
						filename_length,
						central_directory_extra_length,
						comment_length,
						disk_number,
						internal_attr,
						external_attr,
						local_header_offset
				)
				
				# No zip novo
				# Escreve o Central Directory
				zip.write(central_directory)
				# Escreve o nome do arquivo
				zip.write(filename)
				# Escreve o Extra Field
				zip.write(extra)
				# Escreve os comentarios do Central Directory
				zip.write(comment)
				
			# Obtem os dados em bytes do End Of Central Directory
			end_of_central_directory = zip_data[
				end_of_central_directory_offset :
				end_of_central_directory_offset +
				end_of_central_directory_fix_length
			]
			
			# Desempacota o End Of Central Directory inteiro em uma tupla
			end_of_central_directory = struct.unpack(
				end_of_central_directory_format,
				end_of_central_directory
			)
				
			# Quebra a tupla do End Of Central Directory em suas partes nomeadas e identificadas
			(
				signature,
				disk_number,
				disk_start,
				entries_this_disk,
				total_entries,
				cd_size,
				cd_offset,
				comment_length
			) = end_of_central_directory
			
			# Atualiza o offset do Central Directory armazenado no End Of Central Directory
			cd_offset = new_central_directory_offset
			
			# Empacota o End Of Central Directory inteiro em bytes novamente
			end_of_central_directory = struct.pack(
				end_of_central_directory_format,
					signature,
					disk_number,
					disk_start,
					entries_this_disk,
					total_entries,
					cd_size,
					cd_offset,
					comment_length
			)
			
			# Obtem os comentarios do End Of Central Directory
			comment = zip_data[
				end_of_central_directory_offset +
				end_of_central_directory_fix_length :
			]
			
			# No zip novo
			# Escreve o End Of Central Directory
			zip.write(end_of_central_directory)
			# Escreve os comentarios do End Of Central Directory
			zip.write(comment)


########## CLI ##########


# Funcao para argumentos de terminal
def main():
	# Cria o parser
	parser = argparse.ArgumentParser(
		description="Align ZIP/APK entries."
	)
	
	# Adiciona os argumentos do zip de entrada e o zip de saida
	parser.add_argument("input_zip")
	parser.add_argument("output_zip")
	
	# Adiciona os argumentos opcionais para especificar os alinhamentos
	parser.add_argument(
		"-a", "--alignment",
		type=int,
		default=4,
		help="Alignment for regular files (default: 4)."
	)
	parser.add_argument(
		"-s", "--so-alignment",
		type=int,
		default=None,
		help="Alignment for .so files (default: same as alignment)."
	)
	
	# Faz o parsing dos argumentos
	args = parser.parse_args()
	
	# Chama a funcao de alinhamento com as especificacoes fornecidas
	align(
		args.input_zip,
		args.output_zip,
		alignment=args.alignment,
		so_alignment=args.so_alignment
	)
	print(f" ZIP/APK Aligned | {args.alignment} | so {args.so_alignment}")

# Se o script foi executado no terminal, chama a funcao main
if __name__ == "__main__":
    main()