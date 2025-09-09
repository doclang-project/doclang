# Split tables examples

## Example 0

Let's consider the following table:


The table on the left may be split across pages, e.g. as shown on the right:


<table>
    <tr>
        <td>
            Original table:
            <br />
            <img src="./original_table.png" height="900" />
        </td>
        <td>
            Table split across pages:
            <br />
            <img src="./split_table.png" height="900" />
        </td>
    </tr>
</table>

The scenario in the above figure is represented below.

- We introduce a new horizontal thread token, `h_thread_N`, which is used to capture table content that spans pages sidewise,
similarly to the usual thread tokens `thread_N`.
- Only the content that is visible within the page is included in the OTSL token (e.g. see "2025 d").
- When thread linking is resolvable through `ucel`/`lcel` or `h_thread_N`, the `thread_N` token is not used, as it would be redundant.
- When thread linking must be captured, we capture it the earliest possible, i.e. we don't wait for the bottom-most cell
to be reached to add the thread for "Europe" in the example above.

```xml
...
<!-- page 1: -->
<table>
    <otsl><loc_x0/><loc_y0/><loc_x1/><loc_y1/>
        <thread_1/>
        <h_thread_1/>

        <ecel/>                             <ecel/>                      <ecel/><nl/>
        <ecel/>                             <ched/>Continent             <ched/>Country<nl/>
        <rhed/><thread_2/>                  <rhed/>Asia                  <rhed/>Japan<nl/>
    </otsl>
</table>
<page_break/>

<!-- page 2: -->
<table>
    <otsl><loc_x0/><loc_y0/><loc_x1/><loc_y1/>
        <thread_1/>
        <h_thread_2/>

        <rhed/><thread_2/>G7 member         <rhed/><thread_3/>Europe           <rhed/>France<nl/>
        <ucel/>                             <ucel/>                            <rhed/>Germany<nl/>
        <ucel/>                             <ucel/>                            <rhed/>Italy<nl/>
    </otsl>
</table>
<page_break/>

<!-- page 3: -->
<table>
    <otsl><loc_x0/><loc_y0/><loc_x1/><loc_y1/>
        <thread_1/>
        <h_thread_3/>

        <rhed/><thread_2/>                  <rhed/><thread_3/>                 <rhed/>United Kingdom<nl/>
        <ucel/>                             <rhed/>North America               <rhed/>Canada<nl/>
        <ucel/>                             <ucel/>                            <rhed/>United States<nl/>
    </otsl>
</table>
<page_break/>

<!-- page 4: -->
<table>
    <otsl><loc_x0/><loc_y0/><loc_x1/><loc_y1/>
        <h_thread_1/>

        <ched/><h_thread_4/>2025 d          <lcel/>                            <lcel/><nl/>
        <ched/>GDP (PPP) per capita in USD  <ched/>Currency                    <ched/><h_thread_5/>Key l<nl/>
        <fcel/>46,097                       <fcel/>Japanese yen (JPY)          <fcel/>Shigeru Ishiba<nl/>
    </otsl>
</table>
<page_break/>

<!-- page 5: -->
<table>
    <otsl><loc_x0/><loc_y0/><loc_x1/><loc_y1/>
        <h_thread_2/>

        <fcel/>54,465                       <fcel/>Euro (EUR)                  <fcel/>Emmanuel Macron<nl/>
        <fcel/>62,830                       <fcel/>Euro (EUR)                  <fcel/>Friedrich Merz<nl/>
        <fcel/>53,115                       <fcel/>Euro (EUR)                  <fcel/>Giorgia Meloni<nl/>
    </otsl>
</table>
<page_break/>

<!-- page 6: -->
<table>
    <otsl><loc_x0/><loc_y0/><loc_x1/><loc_y1/>
        <h_thread_3/>

        <fcel/>52,518                       <fcel/>Pound sterling (GBP)        <fcel/>Keir Starmer<nl/>
        <fcel/>62,830                       <fcel/>Canadian dollar             <fcel/>Mark Carney<nl/>
        <fcel/>53,115                       <fcel/>United States dollar (USD)  <fcel/>Donald Trump<nl/>
    </otsl>
</table>
<page_break/>

<!-- page 7: -->
<table>
    <otsl><loc_x0/><loc_y0/><loc_x1/><loc_y1/>
        <h_thread_1/>

        <ched/><h_thread_4/>etails          <lcel/>                            <lcel/><nl/>
        <ched/><h_thread_5/>eader           <ched/>Population in millions      <ched/>Area in km2<nl/>
        <fcel/>Prime Minister               <fcel/>125.1                       <fcel/>377,975<nl/>
    </otsl>
</table>
<page_break/>
...
```
