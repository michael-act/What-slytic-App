import pandas as pd
import numpy as np
import emoji

from wordcloud import WordCloud

ONLY_ASCII = False


def cleanData(fileName, ASCII=False):
	'''
	Return: Pesan dalam file text whatsapp yang telah di bersihkan dan
			dikelompokkan berdasarkan kolom
	Parameter: 
	filename -> String berupa nama file text whatsapp
	ASCII -> Bool, apakah spesial karakter dihapus?
	'''

	global ONLY_ASCII
	ONLY_ASCII = ASCII

	# Menyiapkan data text yang siap untuk masuk tahap Cleaning
	chatFile = open(fileName, 'r', encoding='utf-8')
	fileLines = chatFile.readlines()
	chatdf = pd.DataFrame(prepData(fileLines), columns=['date', 'author', 'messages'])

	# Mengubah titik menjadi titik dua agar dapat dibaca sebagai jam:menit
	def addColon(datetime):
		date = datetime[:8]
		hours = ''.join(datetime[9:14].split('.'))
		return f'{date} {hours}'

	chatdf['date'] = chatdf['date'].apply(addColon)

	# Mengubah kolom date menjadi tipe data waktu / datetime
	chatdf['date'] = pd.to_datetime(chatdf['date'], errors='coerce')
	chatdf.dropna(inplace=True)

	if ASCII:
		chatdf['messages'] = chatdf['messages'].str.replace('[^a-zA-Z#]', ' ')

	chatdf['messages'] = formaledWord(chatdf['messages'])
	return chatdf

def formaledWord(messages):
	'''
	Return: Pesan yang telah sedikit dihilangkan kata-kata singkat
	Parameter: messages -> Pandas Series
	'''

	dictClean = pd.read_csv('https://raw.githubusercontent.com/nasalsabila/kamus-alay/master/colloquial-indonesian-lexicon.csv', 
							 usecols=['slang', 'formal'])
	dictClean = dict(zip(dictClean['slang'], dictClean['formal']))
	cleaner = lambda s: ' '.join([dictClean[w.lower()] if w.lower() in dictClean else w.lower() for w in s.split()])
	messages = messages.apply(cleaner)
	return messages

def prepData(fileLines):
	'''
	Return: Sekumpulan baris dan kolom text yang telah di pisah-pisahkan
	Parameter: fileLines -> list
	'''

	chatTable = []
	for chat in fileLines:
		date = chat[:14]
		mess = chat[17:]
		if ':' in mess:
			sep = mess.index(':')
		else:
			chatTable.append([date, 'Whatsapp', mess.rstrip('\n')])
			continue
		author = mess[:sep]
		mess = mess[sep+2:].rstrip('\n')
		chatTable.append([date, author, mess])
	return chatTable

def trackChangePhone(data, phone):
	'''
	Return: Hasil rekam setiap jejak perubahan nomor telepon
	Parameter: 
	data -> DataFrame pesan whatsapp
	phone -> list, berisi kumpulan nomor telepon yang ingin di cari jejaknya
	'''

	# Menyimpan baris dataframe yang berisi pesan oleh Whatsapp terkait 
	# perubahan nomor telepon
	phone = [_.strip('\u200e') for _ in phone]
	keyWord = ' telah diganti ke '
	mess = data[(data['author'] == 'Whatsapp') & (data['messages'].str.contains(keyWord))]
	mess = mess['messages'].str.split(keyWord)

	track = dict.fromkeys(phone, set())
	for m in mess:
		m = [_.strip(u'\u200e') for _ in m]
		for n in phone:
			if n in m:
				track[n].update(m)
	return track

def mainGet(data, keyword='', regex=True):
	'''
	Return: Dataframe yang kolom 'messages' mengandung keyword
	Parameter: 
	data -> Pandas DataFrame
	keyword -> String, kata kunci yang harus muncul pada setiap baris
				pada kolom 'messages'
	'''

	data = data[data['messages'].str.contains(keyword, regex=regex)]
	return data

def getMedia(data):
	return mainGet(data, 'Media tidak disertakan')

def getQuestion(data):
	if ONLY_ASCII:
		print('Cannot Found! Because the messages is only ASCII.')
	else:
		return mainGet(data, '?', regex=False)

def getTag(data):
	if ONLY_ASCII:
		print('Cannot Found! Because the messages is only ASCII.')
	else:
		return mainGet(data, '@62')

def getLink(data):
	if ONLY_ASCII:
		print('Cannot Found! Because the messages is only ASCII.')
	else:
		return mainGet(data, r'(?:(?:https?|ftp):\/\/)?[\w/\-?=%.]+\.[\w/\-?=%.]+')

def getDelMessage(data):
	return mainGet(data, 'pesan ini telah dihapus')

def getProfile(data, people):
	'''
	Return: dict, Berupa kumpulan profil lengkap seseorang dalam grup
	Parameter: 
	data -> Pandas DataFrame
	people -> str, orang yang akan di analisis
	'''
	df = data[data['author'] == people]
	rank = data['author'].value_counts().reset_index()
	profile = {'Name': people, 'ActiveDate': pd.to_datetime(df['date'].iloc[[0, -1]].values), 
			   'MessageSent': df, 'MessageDel': getDelMessage(df),
			   'LinkSent': getLink(df), 'MessageTag': getTag(df),
			   'MessageAsk': getQuestion(df), 'MediaSent': getMedia(df),
			   'EmojiUsed': getEmojiCount(df), 
			   'ActiveRank': rank[rank['index'] == people].index[0] + 1}
	return profile

def getEmojiCount(data):
	'''
	Return: Pandas DataFrame, berisi banyaknya emoji yang digunakan
			setiap orang
	Parameter: data -> Pandas DataFrame
	'''

	if ONLY_ASCII:
		print(f'Cannot Found! Because the messages is only ASCII.')
	else:
		emojis = [each for mess in data['messages'] 
						for each in mess 
						if each in emoji.UNICODE_EMOJI_ENGLISH]
		sr = pd.Series(emojis, name='Emoji').value_counts()
		return sr

def getTimeSeriesMessage(data, time):
	'''
	Return: Pandas Series, berisi banyaknya pesan berdasarkan waktu
	Parameter:
	data -> Pandas DataFrame
	time -> list, tipe waktu yang menjadi dasar (hanya 1)
			['year', 'month', 'day', 'hour']
	'''

	dt = lambda y: getattr(data['date'].dt, y)
	base = [dt(b) for b in time]
	df = data.groupby(by=base)['messages'].count()
	return df

def getWordCloud(messages):
	'''
	Return: Objek berupa gambar
	Parameter:
	messages -> Pandas Series, berisi pesan-pesan
	'''
	
	text = ' '.join(sentence for sentence in messages)
	wordcloud = WordCloud(collocations=False, max_words=2000, max_font_size=200, 
						  random_state=42, width=758, height=512, colormap = 'YlGn')
	wordcloud.generate(text)
	return wordcloud.to_image()

if __name__ == '__main__':
	pass
