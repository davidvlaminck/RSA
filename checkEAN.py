def checkEAN(ean:int):
    """
    Controleer of een EAN-nummer geldig is.
    Returns True of False

    - 1. Lengte: Een Belgisch Aansluitnummer moet bestaan uit 18 cijfers.

    - 2. Prefix: Het nummer moet beginnen met de cijfers "54".

    - 3. Controlecijfer: Het laatste cijfer van het EAN-nummer is een controlecijfer dat wordt berekend op basis van de andere cijfers in het nummer. Dit controlecijfer wordt berekend om de nauwkeurigheid van het nummer te verifiëren en wordt gebruikt om te controleren of het nummer geldig is.

        Berekening van het controlecijfer: De controlecijferberekening omvat de volgende stappen:

        Neem de cijfers op oneven posities (exclusief het controlecijfer) en tel ze op.
        Neem de cijfers op even posities en tel ze op.
        Vermenigvuldig de som van de cijfers op even posities met 3.
        Tel de som van de oneven posities op bij het drievoud van de som van de even posities.
        Het controlecijfer is het kleinste getal dat moet worden toegevoegd aan deze som om een veelvoud van 10 te verkrijgen.
        Validatie: Het controlecijfer wordt vergeleken met het laatste cijfer van het EAN-nummer. Als deze twee niet overeenkomen, is het nummer niet geldig.
    """
    check = True

    # 1. Lengte
    ean_lengte = len(str(ean))
    if ean_lengte != 18:
        print(f'EAN-nummer {ean} telt {ean_lengte} karakters en dit moeten er 18 zijn.')
        check = False

    # 2. Prefix
    ean_prefix = str(ean)[:2]
    if ean_prefix != '54':
        print(f'EAN-nummer {ean} heeft prefix {ean_prefix} en dit moet 54 zijn.')
        check = False

    # 3.
    ean_17 = str(ean)[:17]
    print(f'EAN_17: {ean_17}')

    ean_som_even = 0
    ean_som_oneven = 0
    # Loop over de eerste 17 cijfers (laatste is het controlecijfers)
    for i in range(17):
        print(f'Index: {i}')
        # Tel de even en de oneven cijfers op
        if i%2 == 0:
            print('Even')
            ean_som_even += int(ean_17[i])
            print(f'ean_som_even: {ean_som_even}')
        else:
            print('Oneven')
            ean_som_oneven += int(ean_17[i])
            print(f'ean_som_oneven: {ean_som_oneven}')

    ean_som_even_drievoud = ean_som_even * 3
    print(f'Som van de even posities vermenigvuldigd met 3: {ean_som_even_drievoud}')

    ean_som_even_drievoud_som_oneven = ean_som_even_drievoud + ean_som_oneven
    print(f'Som van het drievoud van de even posities {ean_som_even_drievoud} en de oneven posities {ean_som_oneven} luidt: {ean_som_even_drievoud_som_oneven}')

    ean_controlecijfer = 10 - ean_som_even_drievoud_som_oneven%10 # 10 - de modulo. Dit is het cijfer dat je moet bijtellen om door 10 te delen zonder rest
    print(f'ean controlecijfer: {ean_controlecijfer}')

    ean_laatste_cijfer = str(ean)[-1]
    if int(ean_controlecijfer) != int(ean_laatste_cijfer):
        print(f'EAN-controlecijfer {ean_controlecijfer} stemt niet overeen met het laatste cijfers {ean_laatste_cijfer}.')
        check = False
    else:
        print(f'EAN-nummer {ean} is correct')

    return check

# Maak hier een prompt van
ean = input('Geef een EAN-nummer ter controle: ')
checkEAN(ean)
