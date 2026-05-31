# Form Examples

## Simple key-values

![form-00](./form_00.png)

```xml
<form>
    <form_item>
        <key>Firma:</key>
        <value>Holcim ... GmbH</value>
    </form_item>
    <form_item>
        <key>Werk:</key>
        <value>Scholkholz</value>
    </form_item>
    ...
    <form_item>
        <key>Petrograph. Typ:</key>
        <value>Quartiarer Sand + Kies</value>
    </form_item>
</form>
```

## Nesting forms and using form headings

![form-01](./form_01.png)

```xml
<form>
    <form_heading>
    <marker>14.</marker>Transport Information
    </form_heading>
    <form>
        <form_heading>Land transport ... (Germany)</form_heading>
        <form_item>
            <key>GGVS/GGVE class:</key>
            <value>8</value>
        </form_item>
        <form_item>
            <key>ADR/RID class:</key>
            <value>8</value>
        </form_item>
        ...
    </form>
    <form_item>
        <key>River transport ADN/ADNR</key>
        <value>not examined</value>
    </form_item>
    <form>
        <form_heading>Sea transport IMDG</form_heading>
        ...
    </form>
    ...
    <text>The transport ... considered.</text>
    <text>THESE TRANSPORT ... PACK!</text>
</form>
```

## Fillable form

![form-02](./form_02.png)

```xml
<form>
    <form_item>
        <key>Description</key>
        <value>A.A. Cat</value>
    </form_item>
    <form_item>
        <key>Quant.</key>
        <value></value>
    </form_item>
        <form_item>
        <key>Un</key>
        <value></value>
    </form_item>
    <form_item>
        <key>Measure</key>
        <value></value>
    </form_item>
    <form_item>
        <key>Price (in currency)</key>
        <value></value>
    </form_item>
    <form_item>
        <key>Un</key>
        <value></value>
    </form_item>
    <form_item>
        <key>Total</key>
        <value></value>
    </form_item>
    <text></text>
    <form>
        <form_item>
            <key>Delivery Cost</key>
            <value></value>
        </form_item>
        <form_item>
            <key>Maintenance</key>
            <value></value>
        </form_item>
        ...
    <form>
    <form>
        <form_item>
            <key>Date and time of delivery:</key>
            <value></value>
        </form_item>
        ...
        <form_item>
            <key>Guarantee</key>
            <value></value>
        </form_item>
        <text>Delivery Supplies ... Finance Department</text>
    </form>
    ...
</form>
```

## Example 3

![form-03](./form_03.png)

```xml
<form>
    <form_heading>Information about you</form_heading>
    <form_item>
        <key>*Family Name (Last Name)</key>
        <value>staar</value>
    </form_item>
    <form_item>
        <key>*Given Name (First Name)</key>
        <value>peter</value>
    </form_item>
    <form_item>
        <key>*Middle Name (if applicable)</key>
        <value>WJ</value>
    </form_item>
    <form_item>
        <key>I am in the United States as a:</key>
        <checkbox selected="false">Visitor</checkbox>
        <checkbox selected="false">Student</checkbox>
        <checkbox selected="false">Permanent Resident</checkbox>
        <checkbox selected="false">Other (Specify)</checkbox>
        <value></value>
    <form_item>
    <form_item>
        <key>Country of Citizenship</key>
        <value></value>
    </form_item>
    <form_item>
        <key>*Date of Birth</key>
        <value></value>
    </form_item>
    <form_item>
        <key>Alien Registration Number (A-Number) (if any)</key>
        <value></value>
    </form_item>
    <form_heading>Information About Your Address</form_heading>
    <text>*Present Physical Address ()No Po Boxes</text>
    <form_item>
        <key>*Street ... Name</key>
        <value></value>
    </form_item>
    <form_item>
        <key>Apt.</key>
        <checkbox selected="false"></checkbox>
    </form_item>
    <form_item>
        <key>Ste.</key>
        <checkbox selected="false"></checkbox>
    </form_item>
    ...

</form>
```

## High density form

![form-07](./form_07.png)

```xml
<heading level="1">SEZIONE II A - REDDITI SOGGETTI A IMPOSTA SOSTITUTIVA</heading>
<form>
    <form_heading level="1">M31</form_heading>
    <form_heading level="2">REDDITI DI CAPITALE SOGGETTI AD IMPOSIZIONE SOSTITUTIVA</form_heading>
    <form_item>
    	 <marker>1</marker>
        <key>Tipo</key>
        <value></value>
    </form_item>
    <form_item>
        <marker>2</marker>
        <key>Codice Stato estero</key>
        <value></value>
    </form_item>
    <form_item>
        <marker>3</marker>
        <key>Ammontare reddito</key>
        <value></value>
    </form_item>
    <form_item>
        <marker>4</marker>
        <key>Aliquota %</key>
        <value></value>
    </form_item>
    <form_item>
        <marker>5</marker>
        <key>Credito IVCA</key>
        <value></value>
    </form_item>
    <form_item>
        <marker>6</marker>
        <key>Proventi particolari</key>
        <value></value>
    </form_item>
    <form_item>
        <marker>7</marker>
        <key>Opzione tassazione ordinaria</key>
        <value></value>
    </form_item>

    <form_heading level="1">M32</form_heading>
    <form_heading level="2">PROVENTI DELLE OBBLIGAZIONI NON ASSOGGETTATI A IMPOSTA SOSTITUTIVA</form_heading>
    <form_item>
        <marker>1</marker>
        <key>Ammontare reddito</key>
        <value></value>
    </form_item>
    <form_item>
        <marker>2</marker>
        <key>Aliquota %</key>
        <value></value>
    </form_item>

    <form_heading level="1">M33</form_heading>
    <form_heading level="2">PROVENTI DERIVANTI DA DEPOSITI IN GARANZIA</form_heading>
    <form_item>
        <marker>1</marker>
        <key>Ammontare reddito</key>
        <value></value>
    </form_item>
    ...

</form>
```

## Values without Keys

![form-08](./form_08.png)

```xml
<heading level="1">QUADRO W - Investimenti e attività estere di natura finanziaria o patrimoniale</heading>
<heading level="2">SEZIONE I - DATI RELATIVI AGLI INVESTIMENTI E ALLE ATTIVITA'</heading>
<form>
    <form_heading level="1">W1</form_heading>
    <form_item>
        <marker>1</marker>
        <key>CODICE TITOLO POSSESSO</key>
        <value></value>
    </form_item>
    <form_item>
        <marker>2</marker>
        <key>TIPO CONTRIBUENTE - IVAFE</key>
        <value></value>
    </form_item>
    ...

    <form_heading level="1">W2</form_heading>
    <form_item>
        <marker>1</marker>
        <value></value>
    </form_item>
    <form_item>
        <marker>2</marker>
        <value></value>
    </form_item>
    <form_item>
        <marker>3</marker>
        <value></value>
    </form_item>
    ...

</form>
```

## See lower section of a form with fillable fields, markers, hints.

![form-09](./form_09.png)
```xml
<heading level="1">QUADRO C - Redditi di lavoro dipendente e assimilati</heading>

<form>
    <form_heading level="1">SEZIONE I - REDDITI DI LAVORO DIPENDENTE E ASSIMILATI</form_heading>
    <form_item>
        <key>Casi particolari</key>
        <checkbox selected="false"></checkbox>
        <key>Codice Stato estero</key>
        <value></value>
    </form_item>

    <form_heading level="2">C1</form_heading>
    <form_item>
        <marker>1</marker>
        <key>TIPO</key>
        <value></value>
    </form_item>
    <form_item>
        <marker>2</marker>
        <key>INDETERMINATO/DETERMINATO</key>
        <checkbox selected="false"></checkbox>
    </form_item>
    <form_item>
        <marker>3</marker>
        <key>REDDITO (punti 1,2,3 CU 2025)</key>
        <value>,00</value>
    </form_item>
    <form_item>
        <marker>4</marker>
        <key>ALTRI DATI</key>
        <checkbox selected="false"></checkbox>
    </form_item>

    <form_heading level="2">C2</form_heading>
    <form_item>
        <marker>1</marker>
        <key>TIPO</key>
        <value></value>
    </form_item>
    <form_item>
        <marker>2</marker>
        <key>INDETERMINATO/DETERMINATO</key>
        <checkbox selected="false"></checkbox>
    </form_item>
    <form_item>
        <marker>3</marker>
        <key>REDDITO (punti 1,2,3 CU 2025)</key>
        <value>,00</value>
    </form_item>
    <form_item>
        <marker>4</marker>
        <key>ALTRI DATI</key>
        <checkbox selected="false"></checkbox>
    </form_item>

    <form_heading level="2">C3</form_heading>
    <form_item>
        <marker>1</marker>
        <key>TIPO</key>
        <value></value>
    </form_item>
    <form_item>
        <marker>2</marker>
        <key>INDETERMINATO/DETERMINATO</key>
        <checkbox selected="false"></checkbox>
    </form_item>
    <form_item>
        <marker>3</marker>
        <key>REDDITO (punti 1,2,3 CU 2025)</key>
        <value>,00</value>
    </form_item>
    <form_item>
        <marker>4</marker>
        <key>ALTRI DATI</key>
        <checkbox selected="false"></checkbox>
    </form_item>


    <form_heading level="2">C4</form_heading>
    <form_heading level="3">SOMME PER PREMI DI RISULTATO E WELFARE AZIENDALE</form_heading>
    <form_item>
        <marker>1</marker>
        <key>TIPOLOGIA LIMITE</key>
        <checkbox selected="false"></checkbox>
    </form_item>
    <form_item>
        <marker>2</marker>
        <key>SOMME A TASSAZIONE ORDINARIA</key>
        <value>,00</value>
    </form_item>
    <form_item>
        <marker>3</marker>
        <key>SOMME A IMPOSTA SOSTITUTIVA</key>
        <value>,00</value>
    </form_item>
    ...

</form>
```

## Middle section of a form with A and B choices

![form-19](./form_19_water_damage.png)
```xml
...
<form>
    <form_heading>COCHER LES CASES CONCERNEES</form_heading>
    <form_item>
        <key>La cause du sinistre se situe-t-elle chez vous ?</key>
        <checkbox selected="false"><marker>A</marker>oui</checkbox>
        <checkbox selected="false"><marker>A</marker>non</checkbox>
        <checkbox selected="false"><marker>B</marker>oui</checkbox>
        <checkbox selected="false"><marker>B</marker>non</checkbox>
    </form_item>
    <form_item>
        <key>Êtes-vous assuré en dégâts des eaux ?</key>
        <checkbox selected="false"><marker>A</marker>oui</checkbox>
        <checkbox selected="false"><marker>A</marker>non</checkbox>
        <checkbox selected="false"><marker>B</marker>oui</checkbox>
        <checkbox selected="false"><marker>B</marker>non</checkbox>
    </form_item>
    <form_item>
        <key>Si vous êtes occupant et que vous allez déménager avez-vous donné ou reçu congé ?</key>
        <checkbox selected="false"><marker>A</marker>avant le sinistre</checkbox>
        <checkbox selected="false"><marker>A</marker>après le sinistre</checkbox>
        <checkbox selected="false"><marker>B</marker>avant le sinistre</checkbox>
        <checkbox selected="false"><marker>B</marker>après le sinistre</checkbox>
    </form_item>
    <form_heading>NATURE DES DOMMAGES peinture et/ou papier peint</form_heading>
    <form_item>
        <key>revêtements (sol, mur, plafond)</key>
        <checkbox selected="false"><marker>A</marker>collés</checkbox>
        <checkbox selected="false"><marker>A</marker>agrafés ou cloués</checkbox>
        <checkbox selected="false"><marker>B</marker>collés</checkbox>
        <checkbox selected="false"><marker>B</marker>agrafés ou cloués</checkbox>
    </form_item>
    <form_item>
        <key>Ces aménagements ont-ils été exécutés à vos frais ?</key>
        <checkbox selected="false"><marker>A</marker>oui</checkbox>
        <checkbox selected="false"><marker>A</marker>non</checkbox>
        <checkbox selected="false"><marker>B</marker>oui</checkbox>
        <checkbox selected="false"><marker>B</marker>non</checkbox>
    </form_item>
    <form_item>
        <key>Autres dommages immobiliers (carrelage, parquet, plâtrerie...)</key>
        <checkbox selected="false"><marker>A</marker></checkbox>
        <checkbox selected="false"><marker>B</marker></checkbox>
    </form_item>
    <form_item>
        <key>Objets mobiliers</key>
        <checkbox selected="false"><marker>A</marker></checkbox>
        <checkbox selected="false"><marker>B</marker></checkbox>
    </form_item>
    <form_item>
        <key>Matériels ou marchandises</key>
        <checkbox selected="false"><marker>A</marker></checkbox>
        <checkbox selected="false"><marker>B</marker></checkbox>
    </form_item>
    <form_item>
        <key>Autres dommages</key>
        <value><marker>A</marker><hint>(à préciser)</hint></value>
        <value><marker>B</marker><hint>(à préciser)</hint></value>
    </form_item>
</form>
...
```

## Tabular form with strong 2D value relationship

![form-17](./form_17_tabular_form_with_many_elements.png)
Tabular part of the form:
```xml

<otsl>
<srow>Beiträge zur Altersvorsorge<srow>52</lcel></srow><nl/>
<fcel/>                           <ched/>Steue...Ehemann / Person A<ched/>Ehefrau / Person B<fcel/> <nl/>
<fcel/>Arbeitnehmeranteil laut ...<fcel/>***FORM1***,-             <fcel/>***FORM2***,-     <fcel/>@<nl/>
<fcel/>Beiträge zur landwirtsc ...<fcel/>***FORM3***,-             <fcel/>***FORM4***,-     <fcel/> <nl/>
<fcel/>Beiträge zu gesetzliche ...<fcel/>***FORM5***,-             <fcel/>***FORM6***,-     <fcel/> <nl/>
<fcel/>Erstattete Beiträge und ...<fcel/>***FORM7***,-             <fcel/>***FORM8***,-     <fcel/>@<nl/>
...
</otsl>
...

FORMS:
***FORM1***: <form_item><key>300</key><value></value><hint>EUR</hint></form_item>
***FORM2***: <form_item><key>400</key><value></value><hint>EUR</hint></form_item>
***FORM4***: <form_item><key>401</key><value></value></form_item>
***FORM5***: <form_item><key>302</key><value></value></form_item>
***FORM3***: <form_item><key>301</key><value></value></form_item>
***FORM6***: <form_item><key>402</key><value></value></form_item>
***FORM7***: <form_item><key>309</key><value></value></form_item>
***FORM8***: <form_item><key>409</key><value></value></form_item>
```

## Mix table and form elements

![form-15](./form_15_large_key.png)

```xml
...
<heading>Part III</heading>
<text>Figure Your Credit</text>

<text>10</text>

<otsl>
<ched/>If you checked (in Part l):<ched/>Enter<nl/>
<fcel/>Box 1, 2, 4, or 7<fcel/>$5,000<nl/>
<fcel/>Box 3, 5, or 6<fcel/>$7,500<nl/>
<fcel/>Box 8 or 9<fcel/>$3,750<nl/>
</otsl>

<form_item><key>10</key><value></value></form_item>

<text>11 If you checked (in Part I):</text>
<list>
    <list_item>Box 6, add $5,000 to the taxable disability income of the spouse who was under age 65. Enter the total.</list_item>
    <list_item>Box 2, 4, or 9, enter your taxable disability income.</list_item>
    <list_item>BBox 5, add your taxable disability income to your spouse's taxable disability income. Enter the total.</list_item>
</list>

<form_item><key>11</key><value>.</value></form_item>

<picture><label value="logo"/></picture>
<text>For more details on what to include on line 11, see Figure Your Credit in the instructions.</text>

<text>12 If you completed line 11, enter the smaller of line 10 or line 11. All others, enter the amount from line 10</text>
<form_item><key>12</key><value>74,992</value></form_item>
...
```
