# Form Examples

These examples illustrate the [Fields](../../spec.md#fields) section of the DocLang specification, using `field_region`, `field_item`, and `field_heading` elements.

## Simple key-values

![form-00](./form_00.png)

```xml
<field_region>
    <field_item>
        <key>Firma:</key>
        <value>Holcim ... GmbH</value>
    </field_item>
    <field_item>
        <key>Datum:</key>
        <value>23.08.2019</value>
    </field_item>
    <!--...-->
    <field_item>
        <key>Petrograph. Typ:</key>
        <value>Quartiarer Sand + Kies</value>
    </field_item>
</field_region>
```

## Nesting forms and using form headings

![form-01](./form_01.png)

```xml
<field_region>
    <field_heading>
        <marker>14.</marker>
        Transport Information
    </field_heading>
    <field_region>
        <field_heading>
            Land transport ... (Germany)
        </field_heading>
        <field_item>
            <key>GGVS/GGVE class:</key>
            <value>8</value>
        </field_item>
        <field_item>
            <key>ADR/RID class:</key>
            <value>8</value>
        </field_item>
        <!--...-->
    </field_region>
    <field_item>
        <key>River transport ADN/ADNR</key>
        <value>not examined</value>
    </field_item>
    <field_region>
        <field_heading>
            Sea transport IMDG
        </field_heading>
        <!--...-->
    </field_region>
    <!--...-->
    <text>
        The transport ... considered.
    </text>
    <text>
        THESE TRANSPORT ... PACK!
    </text>
</field_region>
```

## Fillable form

![form-02](./form_02.png)

```xml
<field_region>
    <field_item>
        <key>Description</key>
        <value>A.A. Cat</value>
    </field_item>
    <field_item>
        <key>Quant.</key>
        <value></value>
    </field_item>
    <field_item>
        <key>Un</key>
        <value></value>
    </field_item>
    <field_item>
        <key>Measure</key>
        <value></value>
    </field_item>
    <field_item>
        <key>Price (in currency)</key>
        <value></value>
    </field_item>
    <field_item>
        <key>Un</key>
        <value></value>
    </field_item>
    <field_item>
        <key>Total</key>
        <value></value>
    </field_item>
    <text></text>
    <field_region>
        <field_item>
            <key>Delivery Cost</key>
            <value></value>
        </field_item>
        <field_item>
            <key>Maintenance</key>
            <value></value>
        </field_item>
        <!--...-->
    </field_region>
    <field_region>
        <field_item>
            <key>Date and time of delivery:</key>
            <value></value>
        </field_item>
        <!--...-->
        <field_item>
            <key>Guarantee</key>
            <value></value>
        </field_item>
        <text>
            Delivery Suppl...Finance Department
        </text>
    </field_region>
    <!--...-->
</field_region>
```

## Use of form headings

![form-03](./form_03.png)

```xml
<field_region>
    <field_heading>Information about you</field_heading>
    <field_item>
        <key>
            *Family Name (Last Name)
        </key>
        <value>staar</value>
    </field_item>
    <field_item>
        <key>*Given Name (First Name)</key>
        <value>peter</value>
    </field_item>
    <field_item>
        <key>*Middle Name (if applicable)</key>
        <value>WJ</value>
    </field_item>
    <field_item>
        <key>I am in the United States as a:</key>
        <text><checkbox class="unselected"/>Visitor</text>
        <text><checkbox class="unselected"/>Student</text>
        <text><checkbox class="unselected"/>Permanent Resident</text>
        <text><checkbox class="unselected"/>Other (Specify)</text>
        <value></value>
    </field_item>
    <field_item>
        <key>Country of Citizenship</key>
        <value></value>
    </field_item>
    <field_item>
        <key>*Date of Birth</key>
        <value></value>
    </field_item>
    <field_item>
        <key>Alien Registration Number (A-Number) (if any)</key>
        <value>A-</value>
    </field_item>
    <field_heading>Information About Your Address</field_heading>
    <text>*Present Physical Address ()No Po Boxes</text>
    <field_item>
        <key>*Street ... Name</key>
        <value></value>
    </field_item>
    <field_item>
        <key>Apt.</key>
        <checkbox class="unselected"/>
    </field_item>
    <field_item>
        <key>Ste.</key>
        <checkbox class="unselected"/>
    </field_item>
    <!--...-->

</field_region>
```

## High density form

![form-07](./form_07.png)

```xml
<field_region>
    <field_heading>M31</field_heading>
    <field_heading level="2">REDDITI DI CAPITALE SOGGETTI AD IMPOSIZIONE SOSTITUTIVA</field_heading>
    <field_item>
        <marker>1</marker>
        <key>Tipo</key>
        <value></value>
    </field_item>
    <field_item>
        <marker>2</marker>
        <key>Codice Stato estero</key>
        <value></value>
    </field_item>
    <field_item>
        <marker>3</marker>
        <key>Ammontare reddito</key>
        <value>,00</value>
    </field_item>
    <field_item>
        <marker>4</marker>
        <key>Aliquota %</key>
        <value></value>
    </field_item>
    <field_item>
        <marker>5</marker>
        <key>Credito IVCA</key>
        <value>,00</value>
    </field_item>
    <field_item>
        <marker>6</marker>
        <key>Proventi particolari</key>
        <value></value>
    </field_item>
    <field_item>
        <marker>7</marker>
        <key>Opzione tassazione ordinaria</key>
        <value></value>
    </field_item>

    <field_heading>M32</field_heading>
    <field_heading level="2">PROVENTI DELLE OBBLIGAZIONI NON ASSOGGETTATI A IMPOSTA SOSTITUTIVA</field_heading>
    <field_item>
        <marker>1</marker>
        <key>Ammontare reddito</key>
        <value>,00</value>
    </field_item>
    <field_item>
        <marker>2</marker>
        <key>Aliquota %</key>
        <value></value>
    </field_item>

    <field_heading>M33</field_heading>
    <field_heading level="2">PROVENTI DERIVANTI DA DEPOSITI IN GARANZIA</field_heading>
    <field_item>
        <marker>1</marker>
        <key>Ammontare reddito</key>
        <value>,00</value>
    </field_item>
    <!--...-->

</field_region>
```

## Values without Keys

![form-08](./form_08.png)

```xml
<heading>QUADRO W - Investimenti e...</heading>
<heading level="2">SEZIONE I - DATI RELATIVI...</heading>
<field_region>
    <field_heading>W1</field_heading>
    <field_item>
        <marker>1</marker>
        <key>CODICE TITOLO POSSESSO</key>
        <value></value>
    </field_item>
    <field_item>
        <marker>2</marker>
        <key>TIPO CONTRIBUENTE - IVAFE</key>
        <value></value>
    </field_item>
    <!--...-->

    <field_heading>W2</field_heading>
    <field_item>
        <marker>1</marker>
        <value></value>
    </field_item>
    <field_item>
        <marker>2</marker>
        <value></value>
    </field_item>
    <field_item>
        <marker>3</marker>
        <value></value>
    </field_item>
    <!--...-->

</field_region>
```

## Another complex form deconstructed into field items

![form-09](./form_09.png)

```xml
<heading>QUADRO C - Redditi di lavoro...</heading>

<field_region>
    <field_heading>SEZIONE I - RE...</field_heading>
    <field_item>
        <key>Casi particolari</key>
        <checkbox class="unselected"/>
    </field_item>
    <field_item>
        <key>Codice Stato estero</key>
        <value></value>
    </field_item>

    <field_heading level="2">C1</field_heading>
    <field_item>
        <marker>1</marker>
        <key>TIPO</key>
        <value></value>
    </field_item>
    <field_item>
        <marker>2</marker>
        <key>INDETERMINATO/DETERMINATO</key>
        <checkbox class="unselected"/>
    </field_item>
    <field_item>
        <marker>3</marker>
        <key>REDDITO (punti 1,2,3 CU 2025)</key>
        <value>,00</value>
    </field_item>
    <field_item>
        <marker>4</marker>
        <key>ALTRI DATI</key>
        <checkbox class="unselected"/>
    </field_item>

    <field_heading level="2">C2</field_heading>
    <field_item>
        <marker>1</marker>
        <key>TIPO</key>
        <value></value>
    </field_item>
    <field_item>
        <marker>2</marker>
        <key>INDETERMINATO/DETERMINATO</key>
        <checkbox class="unselected"/>
    </field_item>
    <field_item>
        <marker>3</marker>
        <key>REDDITO (punti 1,2,3 CU 2025)</key>
        <value>,00</value>
    </field_item>
    <field_item>
        <marker>4</marker>
        <key>ALTRI DATI</key>
        <checkbox class="unselected"/>
    </field_item>

    <field_heading level="2">C3</field_heading>
    <field_item>
        <marker>1</marker>
        <key>TIPO</key>
        <value></value>
    </field_item>
    <field_item>
        <marker>2</marker>
        <key>INDETERMINATO/DETERMINATO</key>
        <checkbox class="unselected"/>
    </field_item>
    <field_item>
        <marker>3</marker>
        <key>REDDITO (punti 1,2,3 CU 2025)</key>
        <value>,00</value>
    </field_item>
    <field_item>
        <marker>4</marker>
        <key>ALTRI DATI</key>
        <checkbox class="unselected"/>
    </field_item>

    <field_heading level="2">C4</field_heading>
    <field_heading level="3">SOMME PER PREMI...
    </field_heading>
    <field_item>
        <marker>1</marker>
        <key>TIPOLOGIA LIMITE</key>
        <checkbox class="unselected"/>
    </field_item>
    <field_item>
        <marker>2</marker>
        <key>SOMME A TASSAZIONE ORDINARIA</key>
        <value>,00</value>
    </field_item>
    <field_item>
        <marker>3</marker>
        <key>SOMME A IMPOSTA SOSTITUTIVA</key>
        <value>,00</value>
    </field_item>
    <!--...-->

</field_region>
```

## Middle section of a form with A and B choices

![form-19](./form_19_water_damage.png)

```xml
<!--...-->
<field_region>
    <field_heading>COCHER LES CASES CONCERNEES</field_heading>
    <field_item>
        <key>La cause du sinistre se situe-t-elle chez vous ?</key>
        <text><checkbox class="unselected"/><marker>A</marker>oui</text>
        <text><checkbox class="unselected"/><marker>A</marker>non</text>
        <text><checkbox class="unselected"/><marker>B</marker>oui</text>
        <text><checkbox class="unselected"/><marker>B</marker>non</text>
    </field_item>
    <field_item>
        <key>Êtes-vous assuré en dégâts des eaux ?</key>
        <text><checkbox class="unselected"/><marker>A</marker>oui</text>
        <text><checkbox class="unselected"/><marker>A</marker>non</text>
        <text><checkbox class="unselected"/><marker>B</marker>oui</text>
        <text><checkbox class="unselected"/><marker>B</marker>non</text>
    </field_item>
    <field_item>
        <key>Si vous êtes occupant et que vous allez déménager avez-vous donné ou reçu congé ?</key>
        <text><checkbox class="unselected"/><marker>A</marker>avant le sinistre</text>
        <text><checkbox class="unselected"/><marker>A</marker>après le sinistre</text>
        <text><checkbox class="unselected"/><marker>B</marker>avant le sinistre</text>
        <text><checkbox class="unselected"/><marker>B</marker>après le sinistre</text>
    </field_item>
    <field_heading>NATURE DES DOMMAGES peinture et/ou papier peint</field_heading>
    <field_item>
        <key>revêtements (sol, mur, plafond)</key>
        <text><checkbox class="unselected"/><marker>A</marker>collés</text>
        <text><checkbox class="unselected"/><marker>A</marker>agrafés ou cloués</text>
        <text><checkbox class="unselected"/><marker>B</marker>collés</text>
        <text><checkbox class="unselected"/><marker>B</marker>agrafés ou cloués</text>
    </field_item>
    <field_item>
        <key>Ces aménagements ont-ils été exécutés à vos frais ?</key>
        <text><checkbox class="unselected"/><marker>A</marker>oui</text>
        <text><checkbox class="unselected"/><marker>A</marker>non</text>
        <text><checkbox class="unselected"/><marker>B</marker>oui</text>
        <text><checkbox class="unselected"/><marker>B</marker>non</text>
    </field_item>
    <field_item>
        <key>Autres dommages immobiliers (carrelage, parquet, plâtrerie...)</key>
        <text><checkbox class="unselected"/><marker>A</marker></text>
        <text><checkbox class="unselected"/><marker>B</marker></text>
    </field_item>
    <field_item>
        <key>Objets mobiliers</key>
        <text><checkbox class="unselected"/><marker>A</marker></text>
        <text><checkbox class="unselected"/><marker>B</marker></text>
    </field_item>
    <field_item>
        <key>Matériels ou marchandises</key>
        <text><checkbox class="unselected"/><marker>A</marker></text>
        <text><checkbox class="unselected"/><marker>B</marker></text>
    </field_item>
    <field_item>
        <key>Autres dommages</key>
        <value><marker>A</marker><hint>(à préciser)</hint></value>
        <value><marker>B</marker><hint>(à préciser)</hint></value>
    </field_item>
</field_region>
<!--...-->
```

## Tabular form with strong 2D value relationship

![form-17](./form_17_tabular_form_with_many_elements.png)

```xml
<field_region>
  <table>
  <srow/><text>Beiträge zur Altersvorsorge</text>                                       <srow/>                                                           <srow/><text>52</text>                  <ecel/><nl/>
  <ecel/>                                                                               <ched/><text>Steuerpflichtige Person / Ehemann / Person A</text>  <ched/><text>Ehefrau / Person B</text>  <ecel/><nl/>
  <fcel/><text>Arbeitnehmeranteil laut Nr. 23 a / b der Lohnsteuerbescheinigung</text>  <fcel/><text>*FORM1*,-</text>                                     <fcel/><text>*FORM2*,-</text>           <fcel/><text>e</text><nl/>
  <fcel/><text>Beiträge zur landwirtschaftlichen Alterskasse; zu berufsständ...</text>  <fcel/><text>*FORM3*,-</text>                                     <fcel/><text>*FORM4*,-</text>           <ecel/><nl/>
  <fcel/><text>Beiträge zu gesetzlichen Rentenversicherungen...</text>                  <fcel/><text>*FORM5*,-</text>                                     <fcel/><text>*FORM6*,-</text>           <ecel/><nl/>
  <fcel/><text>Erstattete Beiträge und / oder steuerfreie Zuschüsse zu den...</text>    <fcel/><text>*FORM7*,-</text>                                     <fcel/><text>*FORM8*,-</text>           <fcel/><text>e</text><nl/>
  <!--...-->
  </table>
</field_region>
<!--...-->
```

*FORMS referred above:
*FORM1*: <field_item><key>300</key><value></value><hint>EUR</hint></field_item>
*FORM2*: <field_item><key>400</key><value></value><hint>EUR</hint></field_item>
*FORM4*: <field_item><key>401</key><value></value></field_item>
*FORM5*: <field_item><key>302</key><value></value></field_item>
*FORM3*: <field_item><key>301</key><value></value></field_item>
*FORM6*: <field_item><key>402</key><value></value></field_item>
*FORM7*: <field_item><key>309</key><value></value></field_item>
*FORM8*: <field_item><key>409</key><value></value></field_item>

## Mix table and form elements

![form-15](./form_15_large_key.png)

```xml
<!--...-->
<heading>Part III</heading>
<text>Figure Your Credit</text>
<text>10</text>
<table>
  <ched/><text>If you checked (in Part l):</text><ched/><text>Enter</text><nl/>
  <fcel/><text>Box 1, 2, 4, or 7</text><fcel/><text>$5,000</text><nl/>
  <fcel/><text>Box 3, 5, or 6</text><fcel/><text>$7,500</text><nl/>
  <fcel/><text>Box 8 or 9</text><fcel/><text>$3,750</text><nl/>
</table>
<field_region><field_item><key>10</key><value></value></field_item></field_region>
<text>11 If you checked (in Part I):</text>
<list>
    <ldiv/>
    <text>Box 6, add $5,000 to the taxable...</text>
    <ldiv/>
    <text>Box 2, 4, or 9, enter your taxable...</text>
    <ldiv/>
    <text>BBox 5, add your taxable disabilit...</text>
</list>
<field_region><field_item><key>11</key><value>.</value></field_item></field_region>
<picture><label value="logo"/></picture>
<text>For more details on what to include on line 11...</text>
<text>12 If you completed line 11, enter the smaller...</text>
<field_region><field_item><key>12</key><value>74,992</value></field_item></field_region>
<!--...-->
```
